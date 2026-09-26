import os
import subprocess
import sys

def build():
    print("=======================================================")
    print("Compilando Executável Profissional UEMA FastAccess")
    print("=======================================================\n")
    
    print("1. Verificando e instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    print("\n2. Executando PyInstaller com backends protegidos do Windows...")
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name=UEMA_Internet_FastAccess",
        "--hidden-import=keyring.backends.Windows",
        "--hidden-import=winreg",
        "--hidden-import=ctypes",
        "--hidden-import=logger",
        "--hidden-import=single_instance",
        "--hidden-import=autostart",
        "--collect-all=keyring",
        "--collect-all=plyer",
        "main.py"
    ]
    
    subprocess.check_call(cmd)
    
    print("\n=======================================================")
    print("BUILD CONCLUÍDO COM SUCESSO!")
    print("Executável final: desktop_app/dist/UEMA_Internet_FastAccess.exe")
    print("=======================================================")

if __name__ == "__main__":
    build()
