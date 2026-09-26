import time
import sys
import os
import subprocess
import argparse
import network
import security
import ui
from logger import setup_logger
from single_instance import SingleInstance

logger = setup_logger()
UEMA_TARGET_SSID = "UEMA"
STATE_FILE = None

def _state_path():
    """Arquivo de estado do circuit breaker, persistido em %APPDATA%."""
    appdata = os.getenv('APPDATA', os.path.expanduser('~'))
    return os.path.join(appdata, 'UEMA_FastAccess', 'state.json')

def load_circuit_open_time():
    """Restaura o timestamp de abertura do circuit breaker (0 se inexistente)."""
    try:
        import json
        with open(_state_path(), 'r', encoding='utf-8') as f:
            return float(json.load(f).get('circuit_open_time', 0))
    except Exception:
        return 0.0

def save_circuit_open_time(ts):
    """Persiste o timestamp de abertura do circuit breaker."""
    try:
        import json
        os.makedirs(os.path.dirname(_state_path()), exist_ok=True)
        with open(_state_path(), 'w', encoding='utf-8') as f:
            json.dump({'circuit_open_time': ts}, f)
    except Exception as e:
        logger.debug(f"Não foi possível persistir o estado do circuit breaker: {e}")

def show_notification(title, message):
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="UEMA AutoLogin",
            timeout=5
        )
    except Exception as e:
        logger.debug(f"Falha ao exibir notificação nativa: {e}")

def is_uema_network(ssid):
    """Correspondência exata (case-insensitive), evitando SSIDs falsos como FAKE_UEMA."""
    if not ssid:
        return False
    return ssid.strip().upper() == "UEMA"

def open_config_ui():
    """
    Abre a janela de configuração em um processo separado.
    Tkinter não é thread-safe: criar a janela em uma thread do daemon causa
    crashes intermitentes no Windows; um subprocesso elimina o problema.
    Retorna o objeto Popen ou None em caso de falha.
    """
    try:
        if getattr(sys, 'frozen', False):
            return subprocess.Popen([sys.executable, "--config"])
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.py")
        return subprocess.Popen([sys.executable, ui_path])
    except Exception as e:
        logger.error(f"Falha ao abrir janela de configuração: {e}")
        return None

def run_daemon():
    logger.info("=== UEMA FastAccess Daemon iniciado ===")
    
    last_state = "init"
    consecutive_failures = 0
    circuit_open_time = load_circuit_open_time()
    if circuit_open_time > 0:
        consecutive_failures = 3
    failure_cycles = 0
    ui_process = None

    while True:
        try:
            current_ssid = network.get_current_ssid()

            if not is_uema_network(current_ssid):
                if last_state != "fora":
                    logger.info("Aguardando conexão à rede Wi-Fi UEMA...")
                    last_state = "fora"
                consecutive_failures = 0
                time.sleep(15)
                continue

            # 1. Verifica se já há conectividade ativa
            if network.check_internet():
                if last_state != "online":
                    logger.info(f"Conectado ao Wi-Fi ({current_ssid}) com internet ativa.")
                    last_state = "online"
                consecutive_failures = 0
                time.sleep(20)
                continue

            # 2. Mecanismo de Circuit Breaker (Disjuntor de Falhas)
            if consecutive_failures >= 3:
                now = time.time()
                # Se o disjuntor abriu há menos de 5 minutos (300s), entra em espera prolongada
                if now - circuit_open_time < 300:
                    time.sleep(30)
                    continue
                else:
                    # Reseta para permitir uma nova tentativa após o período de esfriamento
                    logger.info("Período de cooldown do Circuit Breaker encerrado. Tentando novamente...")
                    consecutive_failures = 0

            # 3. Detecta portal cativo
            if network.is_captive_portal():
                user, pwd = security.get_credentials()

                if not user or not pwd:
                    if ui_process is not None and ui_process.poll() is not None:
                        # Janela fechada (com ou sem cadastro): permite solicitar de novo
                        ui_process = None
                    if ui_process is None:
                        logger.warning("Credenciais ausentes no cofre. Solicitando cadastro via UI...")
                        show_notification("UEMA Wi-Fi", "Cadastre suas credenciais para login automático.")
                        ui_process = open_config_ui()
                    time.sleep(10)
                    continue

                logger.info("Portal cativo detectado. Enviando credenciais...")
                show_notification("UEMA Wi-Fi", "Autenticando automaticamente...")
                
                success = network.do_login(user, pwd)
                
                if success:
                    logger.info("Autenticação concluída com sucesso! Internet liberada.")
                    show_notification("UEMA Wi-Fi", "Conectado com sucesso à rede UEMA!")
                    last_state = "online"
                    consecutive_failures = 0
                    failure_cycles = 0
                    save_circuit_open_time(0)
                else:
                    consecutive_failures += 1
                    logger.warning(f"Falha de autenticação (Tentativa {consecutive_failures}/3).")

                    if consecutive_failures >= 3:
                        circuit_open_time = time.time()
                        save_circuit_open_time(circuit_open_time)
                        failure_cycles += 1
                        logger.error("Circuit Breaker ativado. Suspendendo requisições por 5 minutos.")

                        if failure_cycles >= 2:
                            # Falhas persistentes mesmo após cooldown: a senha
                            # provavelmente foi trocada no SIGUEMA. Remove só a
                            # senha (mantém o usuário) e reabre o cadastro.
                            failure_cycles = 0
                            consecutive_failures = 0
                            security.delete_password()
                            logger.warning("Senha removida do cofre. Solicitando recadastro.")
                            show_notification(
                                "UEMA Wi-Fi",
                                "Senha rejeitada pelo portal. Atualize suas credenciais."
                            )
                            if ui_process is None or ui_process.poll() is not None:
                                ui_process = open_config_ui()
                        else:
                            show_notification(
                                "UEMA Wi-Fi",
                                "Credenciais rejeitadas repetidamente. Nova tentativa em 5 minutos."
                            )
                    else:
                        show_notification("UEMA Wi-Fi", "Falha no login. Nova tentativa em breve.")

                    last_state = "falha"

        except Exception as e:
            logger.error(f"Exceção não tratada no loop principal: {e}", exc_info=True)

        time.sleep(12)

def main():
    parser = argparse.ArgumentParser(description="UEMA Internet FastAccess Daemon")
    parser.add_argument("--config", action="store_true", help="Abre a janela de configuração de credenciais")
    args = parser.parse_args()

    # Se chamado com --config, abre a interface e sai
    if args.config:
        ui.ask_credentials()
        sys.exit(0)

    # Controle de Instância Única via Mutex
    single_instance = SingleInstance()
    if single_instance.is_already_running():
        logger.warning("Uma instância do UEMA FastAccess já está em execução. Encerrando duplicata.")
        sys.exit(0)

    try:
        # Se for a primeiríssima execução e não houver credenciais, abre a UI primeiro
        saved_user, _ = security.get_credentials()
        if not saved_user:
            ui.ask_credentials()

        run_daemon()
    finally:
        single_instance.release()

if __name__ == "__main__":
    main()
