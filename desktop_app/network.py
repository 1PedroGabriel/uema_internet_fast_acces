import subprocess
import requests
import socket
import re
import sys
import time
from logger import setup_logger

logger = setup_logger()

# Parâmetros oficiais do Captive Portal da UEMA
LOGIN_URL = "http://172.25.50.10/auth/index.html/u"
PRIMARY_PROBE = "http://www.msftconnecttest.com/connecttest.txt"
SECONDARY_PROBE = "http://clients3.google.com/generate_204"
USER_FIELD = "user"
PASS_FIELD = "password"

def is_in_uema_subnet():
    """
    SEGURANÇA (Anti-Evil Twin / Rogue AP):
    Como o portal da UEMA recebe a senha por HTTP puro no IP 172.25.50.10,
    precisamos garantir que a máquina está fisicamente na sub-rede legítima
    da universidade (172.25.x.x) antes de disparar qualquer credencial.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Identifica a interface de rede que tem rota para o gateway da UEMA
        s.connect(("172.25.50.10", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Verifica se o IP local obtido via DHCP pertence à rede institucional
        if local_ip.startswith("172.25."):
            return True
        else:
            logger.warning(
                f"[SEGURANÇA] IP local ({local_ip}) não pertence à faixa UEMA (172.25.x.x). "
                "Possível rede falsa ou Evil Twin. Autenticação cancelada."
            )
            return False
    except Exception as e:
        logger.debug(f"Falha ao validar sub-rede local: {e}")
        return False

def get_current_ssid():
    """
    Obtém o SSID do Wi-Fi conectado no Windows com expressão regular precisa,
    evitando colisões com BSSID ou outros adaptadores.
    """
    try:
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'interfaces'],
                startupinfo=startupinfo,
                stderr=subprocess.DEVNULL
            ).decode('utf-8', errors='ignore')
            
            match = re.search(r'^\s*SSID\s*:\s*(.+)$', output, re.MULTILINE)
            if match:
                ssid = match.group(1).strip()
                return ssid if ssid else None
        else:
            output = subprocess.check_output(['iwgetid', '-r'], stderr=subprocess.DEVNULL)
            return output.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        logger.debug(f"Exceção ao obter SSID: {e}")
        return None
    return None

def check_internet():
    """
    Dual-Probe Failover:
    1. Testa o probe primário da Microsoft.
    2. Em caso de falha de resolução DNS, recorre ao probe secundário do Google.
    Retorna True se há conectividade real à internet.
    """
    try:
        response = requests.get(PRIMARY_PROBE, timeout=4)
        if response.status_code == 200 and "Microsoft Connect Test" in response.text:
            return True
    except requests.exceptions.RequestException:
        pass

    try:
        response = requests.get(SECONDARY_PROBE, timeout=4)
        if response.status_code == 204:
            return True
    except requests.exceptions.RequestException:
        pass

    return False

def is_captive_portal():
    """
    Verifica se estamos conectados ao Wi-Fi mas bloqueados pelo portal.
    Faz 2 tentativas espaçadas para evitar falsos positivos durante negociação DHCP.
    """
    if check_internet():
        return False

    time.sleep(2)
    return not check_internet()

def do_login(username, password):
    """
    Realiza o fluxo completo de autenticação com handshake:
    1. Valida se a sub-rede local é legítima (Anti-Evil Twin).
    2. Acessa a página de redirecionamento para capturar cookies/sessão.
    3. Submete o POST com o cabeçalho Referer correto para evitar bloqueios 403.
    4. Confirma se a internet foi liberada após o envio.
    """
    # Verificação de segurança de rede
    if not is_in_uema_subnet():
        return False

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': LOGIN_URL
    })

    try:
        logger.info(f"Iniciando handshake com o gateway da UEMA ({LOGIN_URL})...")
        try:
            session.get(PRIMARY_PROBE, timeout=5, allow_redirects=True)
        except requests.exceptions.RequestException:
            pass

        payload = {
            USER_FIELD: username,
            PASS_FIELD: password,
        }

        response = session.post(LOGIN_URL, data=payload, timeout=8)
        logger.info(f"POST enviado. Código de resposta HTTP: {response.status_code}")
        
        # Pausa para aplicação das regras no firewall
        time.sleep(2)

        success = check_internet()
        if success:
            logger.info("Internet confirmada liberada após autenticação.")
        else:
            logger.warning("POST enviado, mas a internet não respondeu ao teste de conectividade.")
        return success
    except Exception as e:
        logger.error(f"Erro na requisição de autenticação: {e}")
        return False
