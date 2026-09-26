import subprocess
import requests
import re
import sys
import time

# Parâmetros oficiais do Captive Portal da UEMA
LOGIN_URL = "http://172.25.50.10/auth/index.html/u"
PROBE_URL = "http://www.msftconnecttest.com/connecttest.txt"
USER_FIELD = "user"
PASS_FIELD = "password"

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
            
            # Procura por linhas que começam exatamente com "SSID" (ignora BSSID)
            match = re.search(r'^\s*SSID\s*:\s*(.+)$', output, re.MULTILINE)
            if match:
                ssid = match.group(1).strip()
                return ssid if ssid else None
        else:
            output = subprocess.check_output(['iwgetid', '-r'], stderr=subprocess.DEVNULL)
            return output.decode('utf-8', errors='ignore').strip()
    except Exception:
        return None
    return None

def check_internet():
    """
    Retorna True se há conectividade real com a internet.
    Retorna False se estiver bloqueado pelo portal ou sem rede.
    """
    try:
        # Usa o teste oficial do Windows que a UEMA intercepta
        response = requests.get(PROBE_URL, timeout=4)
        if response.status_code == 200 and "Microsoft Connect Test" in response.text:
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def is_captive_portal():
    """
    Verifica se estamos conectados ao Wi-Fi mas bloqueados pelo portal.
    Faz 2 tentativas espaçadas para evitar falsos positivos durante negociação DHCP.
    """
    if check_internet():
        return False

    # Pequena pausa caso a interface acabou de conectar e o DHCP esteja atribuindo IP
    time.sleep(2)
    return not check_internet()

def do_login(username, password):
    """
    Realiza o fluxo completo de autenticação com handshake:
    1. Acessa a página de redirecionamento para capturar cookies/sessão inicial.
    2. Submete o POST com o cabeçalho Referer correto para evitar bloqueios 403.
    3. Confirma se a internet foi liberada após o envio.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': LOGIN_URL
    })

    try:
        # 1. Visita o portal para estabelecer sessão e pegar cookies de redirecionamento
        try:
            session.get(PROBE_URL, timeout=5, allow_redirects=True)
        except requests.exceptions.RequestException:
            pass

        # 2. Prepara o payload oficial
        payload = {
            USER_FIELD: username,
            PASS_FIELD: password,
        }

        # 3. Dispara o POST de autenticação
        response = session.post(LOGIN_URL, data=payload, timeout=8)
        
        # 4. Aguarda 2 segundos para o roteador UEMA aplicar as regras no firewall
        time.sleep(2)

        # 5. Validação real de liberação de tráfego
        return check_internet()
    except Exception as e:
        print(f"Erro no handshake de autenticação: {e}")
        return False
