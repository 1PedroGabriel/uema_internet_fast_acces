import os
import subprocess
import sys

def build():
    print("Iniciando a compilação do executável UEMA Fast Access...")
    
    # Verifica se os requisitos estão instalados
    print("1. Instalando/Verificando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Comando do PyInstaller
    # --noconsole: Executa em background (sem terminal preto irritante)
    # --onefile: Empacota tudo em um único .exe
    # --name: Nome do aplicativo gerado
    print("2. Construindo o executável com PyInstaller...")
    subprocess.check_call([
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name", "UEMA_Internet_FastAccess",
        "main.py"
    ])
    
    print("\n=======================================================")
    print("CONCLUÍDO! O seu executável está na pasta 'dist/'.")
    print("Você pode distribuir o arquivo 'UEMA_Internet_FastAccess.exe' para os usuários.")
    print("=======================================================")

if __name__ == "__main__":
    build()
