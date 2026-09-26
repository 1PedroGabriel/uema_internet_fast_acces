import sys
import os

APP_NAME = "UEMA_Internet_FastAccess"

def set_autostart(enable=True):
    """
    Ativa ou desativa a inicialização automática com o Windows via Registro (HKCU),
    sem exigir privilégios de administrador.
    """
    if sys.platform != "win32":
        return False

    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(key, sub_key, 0, winreg.KEY_SET_VALUE) as reg_key:
            if enable:
                # Obtém o caminho do executável (.exe) ou do script atual
                exe_path = os.path.abspath(sys.argv[0])
                if not exe_path.endswith(".exe"):
                    # Se rodando em desenvolvimento com python
                    exe_path = f'"{sys.executable}" "{os.path.abspath("main.py")}"'
                else:
                    exe_path = f'"{exe_path}"'
                winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(reg_key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"Erro ao configurar inicialização automática: {e}")
        return False

def is_autostart_enabled():
    if sys.platform != "win32":
        return False

    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, sub_key, 0, winreg.KEY_READ) as reg_key:
            winreg.QueryValueEx(reg_key, APP_NAME)
            return True
    except Exception:
        return False
