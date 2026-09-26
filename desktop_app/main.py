import time
import sys
import threading
import network
import security
import ui

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
    except Exception:
        pass

def is_uema_network(ssid):
    if not ssid:
        return False
    # A UEMA transmite principalmente o SSID "UEMA"
    return "UEMA" in ssid.upper()

def run_daemon():
    print("[UEMA FastAccess] Monitor de rede iniciado em segundo plano.")
    
    last_state = "init"
    last_attempt_time = 0
    prompt_open = False

    while True:
        try:
            current_ssid = network.get_current_ssid()

            if not is_uema_network(current_ssid):
                if last_state != "fora":
                    print("[UEMA FastAccess] Aguardando conexão à rede Wi-Fi UEMA...")
                    last_state = "fora"
                time.sleep(15)
                continue

            # Estamos na rede UEMA: verificar conectividade real
            has_internet = network.check_internet()
            
            if has_internet:
                if last_state != "online":
                    print(f"[UEMA FastAccess] Conectado ao Wi-Fi ({current_ssid}) com internet ativa.")
                    last_state = "online"
                time.sleep(20)
                continue

            # Sem internet na rede UEMA: verificar se é captive portal
            if network.is_captive_portal():
                user, pwd = security.get_credentials()

                if not user or not pwd:
                    if not prompt_open:
                        prompt_open = True
                        show_notification("UEMA Wi-Fi", "Cadastre suas credenciais para login automático.")
                        # Abre a interface de cadastro sem travar o loop para sempre
                        ui_thread = threading.Thread(target=ui.ask_credentials)
                        ui_thread.daemon = True
                        ui_thread.start()
                    time.sleep(10)
                    continue
                else:
                    prompt_open = False

                # Rate limiting de tentativas de login: esperar no mínimo 30s entre tentativas falhas
                now = time.time()
                if now - last_attempt_time >= 30:
                    last_attempt_time = now
                    print("[UEMA FastAccess] Portal Cativo detectado. Enviando autenticação...")
                    show_notification("UEMA Wi-Fi", "Autenticando automaticamente...")
                    
                    success = network.do_login(user, pwd)
                    
                    if success:
                        print("[UEMA FastAccess] Autenticação bem-sucedida! Internet liberada.")
                        show_notification("UEMA Wi-Fi", "Autenticado com sucesso! Internet liberada.")
                        last_state = "online"
                    else:
                        print("[UEMA FastAccess] Falha na autenticação. Verifique suas credenciais.")
                        show_notification("UEMA Wi-Fi", "Falha no login. Verifique sua senha do SIGUEMA.")
                        last_state = "falha"

        except Exception as e:
            print(f"[UEMA FastAccess] Exceção no loop: {e}")

        time.sleep(12)

if __name__ == "__main__":
    # Se iniciado sem credenciais cadastradas, exibe a interface logo no início
    saved_user, _ = security.get_credentials()
    if not saved_user:
        ui.ask_credentials()

    run_daemon()
