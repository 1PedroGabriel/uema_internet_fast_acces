import time
import sys
import threading
import argparse
import network
import security
import ui
from logger import setup_logger
from single_instance import SingleInstance

logger = setup_logger()
UEMA_TARGET_SSID = "UEMA"

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
    if not ssid:
        return False
    return "UEMA" in ssid.upper()

def run_daemon():
    logger.info("=== UEMA FastAccess Daemon iniciado ===")
    
    last_state = "init"
    consecutive_failures = 0
    circuit_open_time = 0
    prompt_open = False

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
                    if not prompt_open:
                        prompt_open = True
                        logger.warning("Credenciais ausentes no cofre. Solicitando cadastro via UI...")
                        show_notification("UEMA Wi-Fi", "Cadastre suas credenciais para login automático.")
                        ui_thread = threading.Thread(target=ui.ask_credentials)
                        ui_thread.daemon = True
                        ui_thread.start()
                    time.sleep(10)
                    continue
                else:
                    prompt_open = False

                logger.info("Portal cativo detectado. Enviando credenciais...")
                show_notification("UEMA Wi-Fi", "Autenticando automaticamente...")
                
                success = network.do_login(user, pwd)
                
                if success:
                    logger.info("Autenticação concluída com sucesso! Internet liberada.")
                    show_notification("UEMA Wi-Fi", "Conectado com sucesso à rede UEMA!")
                    last_state = "online"
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    logger.warning(f"Falha de autenticação (Tentativa {consecutive_failures}/3).")
                    
                    if consecutive_failures >= 3:
                        circuit_open_time = time.time()
                        logger.error("Circuit Breaker ativado. Suspendendo requisições por 5 minutos.")
                        show_notification(
                            "UEMA Wi-Fi",
                            "Credenciais rejeitadas repetidamente. Verifique sua senha do SIGUEMA."
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
