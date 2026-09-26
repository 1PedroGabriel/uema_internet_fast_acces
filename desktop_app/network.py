import subprocess
import requests
import sys

# =====================================================================
# CONFIGURAÇÃO DO DESENVOLVEDOR:
# Você precisará usar o F12 (Aba Network/Rede) do seu navegador
# ao fazer login manualmente na rede da UEMA para descobrir a URL
# exata de POST e os nomes dos campos de usuário e senha.
# =====================================================================
LOGIN_URL = "https://SEU_PORTAL_DA_UEMA.br/login" # <- SUBSTITUA AQUI
USER_FIELD = "username"                           # <- SUBSTITUA AQUI
PASS_FIELD = "password"                           # <- SUBSTITUA AQUI
# =====================================================================

def get_current_ssid():
    """Obtém o nome da rede Wi-Fi atual do sistema operacional."""
    try:
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], startupinfo=startupinfo)
        else:
            # Comando genérico para Linux/Mac
            result = subprocess.check_output(['iwgetid', '-r'])
        
        result = result.decode('utf-8', errors='ignore')
        for line in result.split('\n'):
            if " SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
    except Exception:
        return None
    return None

def needs_login():
    """
    Verifica se a internet está bloqueada por um captive portal.
    O Google possui um endpoint projetado especificamente para isso.
    """
    try:
        # Se retornar 204 (No Content), temos acesso direto à internet.
        # Se retornar 200, fomos redirecionados para o portal da UEMA.
        response = requests.get("http://clients3.google.com/generate_204", timeout=5)
        return response.status_code != 204
    except requests.exceptions.RequestException:
        # Sem internet de forma geral, pode estar bloqueado ou desconectado.
        return True

def do_login(username, password):
    """
    Envia as credenciais para o portal da UEMA de forma silenciosa.
    """
    if "SEU_PORTAL_DA_UEMA" in LOGIN_URL:
        print("ERRO: O desenvolvedor precisa configurar a LOGIN_URL no arquivo network.py")
        return False

    payload = {
        USER_FIELD: username,
        PASS_FIELD: password,
        # Se houver checkbox de "aceito os termos", você pode precisar adicionar:
        # "terms": "accepted", "agree": "true", etc. (Verifique no F12 do navegador)
    }
    
    try:
        # O verify=True é CRUCIAL para segurança, evita ataques Man-in-the-Middle (Evil Twin)
        session = requests.Session()
        response = session.post(LOGIN_URL, data=payload, verify=True, timeout=10)
        
        # Após o POST, verificamos se agora temos internet
        return not needs_login()
    except Exception as e:
        print(f"Erro na requisição de login: {e}")
        return False
