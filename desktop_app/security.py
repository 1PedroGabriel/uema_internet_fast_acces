import keyring
import keyring.backends.Windows
import sys

SERVICE_NAME = "UEMA_Wifi_AutoLogin"
USER_KEY = "saved_username"

def _ensure_backend():
    """Garante que o backend do Windows Vault está ativo no executável compilado."""
    try:
        if sys.platform == "win32":
            keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
    except Exception:
        pass

def save_credentials(username, password):
    """
    Salva as credenciais no cofre do sistema operacional.
    Retorna True se salvou com sucesso.
    """
    _ensure_backend()
    try:
        keyring.set_password(SERVICE_NAME, USER_KEY, username)
        keyring.set_password(SERVICE_NAME, username, password)
        return True
    except Exception as e:
        print(f"Erro ao salvar credenciais no keyring: {e}")
        return False

def get_credentials():
    """
    Recupera as credenciais de forma segura.
    Retorna (username, password) ou (None, None).
    """
    _ensure_backend()
    try:
        username = keyring.get_password(SERVICE_NAME, USER_KEY)
        if username:
            password = keyring.get_password(SERVICE_NAME, username)
            return username, password
    except Exception as e:
        print(f"Erro ao obter credenciais do keyring: {e}")
    return None, None
