import keyring

# Nome do "Cofre" no gerenciador de credenciais do Sistema Operacional
SERVICE_NAME = "UEMA_Wifi_AutoLogin"
USER_KEY = "saved_username"

def save_credentials(username, password):
    """
    Salva as credenciais de forma segura usando o gerenciador de senhas do SO
    (ex: Windows Credential Manager, macOS Keychain).
    NUNCA salva em texto plano.
    """
    # Salvamos o nome de usuário usando uma chave fixa
    keyring.set_password(SERVICE_NAME, USER_KEY, username)
    # Salvamos a senha associada ao nome de usuário
    keyring.set_password(SERVICE_NAME, username, password)

def get_credentials():
    """
    Recupera as credenciais de forma segura do cofre do SO.
    Retorna (username, password) ou (None, None) se não existir.
    """
    username = keyring.get_password(SERVICE_NAME, USER_KEY)
    if username:
        password = keyring.get_password(SERVICE_NAME, username)
        return username, password
    return None, None
