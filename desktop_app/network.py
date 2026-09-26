import subprocess
import requests
import sys

# Parâmetros oficiais do Captive Portal da UEMA (Extraídos do HTML original)
LOGIN_URL = "http://172.25.50.10/auth/index.html/u"
USER_FIELD = "user"
PASS_FIELD = "password"

def get_current_ssid():
    """Obtém o nome da rede Wi-Fi atual do sistema operacional."""
    try:
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], startupinfo=startupinfo)
        else:
            result = subprocess.check_output(['iwgetid', '-r'])
        
        result = result.decode('utf-8', errors='ignore')
        for line in result.split('\n'):
            if " SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
    except Exception:
        return None
    return None

def needs_login():
    """Verifica se a internet está bloqueada por um captive portal."""
    try:
        response = requests.get("http://clients3.google.com/generate_204", timeout=5)
        return response.status_code != 204
    except requests.exceptions.RequestException:
        return True

def do_login(username, password):
    """Envia as credenciais para o portal da UEMA de forma silenciosa."""
    payload = {
        USER_FIELD: username,
        PASS_FIELD: password,
    }
    
    try:
        session = requests.Session()
        # O portal real da UEMA roda em HTTP interno (172.25.50.10)
        response = session.post(LOGIN_URL, data=payload, timeout=10)
        
        # Após o POST, verificamos se agora temos internet
        return not needs_login()
    except Exception as e:
        print(f"Erro na requisição de login: {e}")
        return False
