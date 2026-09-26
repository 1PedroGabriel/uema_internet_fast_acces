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
        else:
            print(f"Aviso: plataforma '{sys.platform}' sem backend forçado; "
                  "o keyring pode usar armazenamento menos seguro.")
    except Exception as e:
        print(f"Aviso: não foi possível forçar o backend WinVault: {e}")

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

def delete_password():
    """
    Remove apenas a senha do cofre, mantendo o usuário para pré-preenchimento.
    Usado quando o portal rejeita a senha repetidamente (ex.: troca no SIGUEMA).
    """
    _ensure_backend()
    try:
        username = keyring.get_password(SERVICE_NAME, USER_KEY)
        if username:
            keyring.delete_password(SERVICE_NAME, username)
        return True
    except Exception as e:
        print(f"Erro ao remover senha do keyring: {e}")
        return False

def delete_credentials():
    """Remove usuário e senha do cofre (esquecimento completo)."""
    _ensure_backend()
    ok = True
    try:
        username = keyring.get_password(SERVICE_NAME, USER_KEY)
        if username:
            keyring.delete_password(SERVICE_NAME, username)
    except Exception as e:
        print(f"Erro ao remover senha do keyring: {e}")
        ok = False
    try:
        keyring.delete_password(SERVICE_NAME, USER_KEY)
    except Exception:
        pass  # chave inexistente é aceitável
    return ok
