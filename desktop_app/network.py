import subprocess
import requests
import socket
import re
import sys
import time
import ipaddress
from urllib.parse import urljoin, urlparse
from logger import setup_logger

logger = setup_logger()

# Fallback: endereço do Captive Portal da UEMA observado no campus.
# O endereço real é descoberto dinamicamente a cada conexão (ver do_login),
# pois pode variar entre campi/controladores.
LOGIN_URL = "http://172.25.50.10/auth/index.html/u"
PORTAL_FALLBACK_HOST = "172.25.50.10"
PRIMARY_PROBE = "http://www.msftconnecttest.com/connecttest.txt"
SECONDARY_PROBE = "http://clients3.google.com/generate_204"
USER_FIELD = "user"
PASS_FIELD = "password"

def is_private_network_ip(ip_str):
    """True se o IP pertence a faixas privadas/locais (RFC1918, loopback, link-local)."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False

def is_in_uema_subnet():
    """
    SEGURANÇA (Anti-Evil Twin):
    Garante que a máquina está em uma rede privada antes de enviar credenciais.
    IMPORTANTE: o IP do cliente na rede UEMA pode ser 10.x.x.x (observado
    10.101.x.x) enquanto o controlador do portal usa 172.25.x.x. Por isso a
    validação aceita qualquer faixa privada; a URL final do portal é
    descoberta dinamicamente e validada separadamente em do_login().
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Identifica a interface que tem rota para o controlador da UEMA
            s.connect((PORTAL_FALLBACK_HOST, 80))
        except OSError:
            # Fallback: qualquer rota externa serve para identificar a interface ativa
            s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        if is_private_network_ip(local_ip):
            return True
        logger.warning(
            f"[SEGURANÇA] IP local ({local_ip}) não é privado. "
            "Possível rede falsa ou Evil Twin. Autenticação cancelada."
        )
        return False
    except Exception as e:
        logger.debug(f"Falha ao validar sub-rede local: {e}")
        return False

def discover_portal_url(session):
    """
    Descobre dinamicamente a URL de autenticação do portal cativo:
    segue o redirecionamento do probe e extrai o 'action' do formulário.
    Só aceita destino HTTP em IP privado (anti-phishing). Retorna None se
    não conseguir descobrir com segurança.
    """
    try:
        probe_resp = session.get(PRIMARY_PROBE, timeout=5, allow_redirects=True)
    except requests.exceptions.RequestException:
        return None

    if probe_resp.status_code == 200 and "Microsoft Connect Test" in probe_resp.text:
        return None  # Internet já livre, não há portal

    form_match = re.search(
        r'<form[^>]*action=["\']([^"\']+)["\']', probe_resp.text, re.IGNORECASE
    )
    if not form_match:
        return None

    discovered = urljoin(probe_resp.url, form_match.group(1))
    parsed = urlparse(discovered)
    if parsed.scheme == 'http' and is_private_network_ip(parsed.hostname or ''):
        return discovered

    logger.warning(
        f"[SEGURANÇA] URL de portal descoberta rejeitada (não é IP privado HTTP): {discovered}"
    )
    return None

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
            ).decode('mbcs', errors='ignore')
            
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

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': LOGIN_URL
        })

        try:
            # Descobre a URL real do portal (muda conforme campus/controlador);
            # usa o fallback fixo se a descoberta falhar
            target_url = discover_portal_url(session) or LOGIN_URL
            if target_url != LOGIN_URL:
                logger.info(f"Portal descoberto dinamicamente: {target_url}")
            logger.info(f"Iniciando handshake com o gateway da UEMA ({target_url})...")

            payload = {
                USER_FIELD: username,
                PASS_FIELD: password,
            }

            response = session.post(target_url, data=payload, timeout=8)
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
