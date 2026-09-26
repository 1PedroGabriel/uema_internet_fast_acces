import time
import sys
import network
import security
import ui

# Redes alvo. O script só tentará logar se o SSID contiver um desses nomes.
# Ajuste conforme os nomes reais da rede Wi-Fi da UEMA.
UEMA_NETWORKS = ["UEMA", "UEMA-WIFI", "UEMA_GUEST", "UEMA ALUNOS"]

def show_notification(title, message):
    try:
        # Tenta usar o Plyer para enviar uma notificação nativa do SO
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="UEMA AutoLogin",
            timeout=5
        )
    except Exception as e:
        print(f"Log: {title} - {message}")

def is_uema_network(ssid):
    if not ssid:
        return False
    ssid_upper = ssid.upper()
    return any(net in ssid_upper for net in UEMA_NETWORKS)

def run_daemon():
    print("Serviço UEMA AutoLogin iniciado em background.")
    
    while True:
        try:
            current_ssid = network.get_current_ssid()

            # 1. Estou na internet da UEMA?
            if is_uema_network(current_ssid):
                
                # 2. Estou logado? (Verifica acesso real à web)
                if network.needs_login():
                    print(f"Portal detectado na rede: {current_ssid}")
                    
                    # 3. Use as credenciais registradas
                    user, pwd = security.get_credentials()
                    
                    # 4. Caso não tenha, gera notificação/janela para registrar
                    if not user or not pwd:
                        show_notification("UEMA Wi-Fi", "Credenciais necessárias. Clique/Abra para registrar.")
                        ui.ask_credentials()
                        user, pwd = security.get_credentials() # Tenta pegar novamente
                    
                    # Se agora temos credenciais, faz o login
                    if user and pwd:
                        show_notification("UEMA Wi-Fi", "Autenticando automaticamente...")
                        success = network.do_login(user, pwd)
                        
                        if success:
                            show_notification("UEMA Wi-Fi", "Conectado com sucesso!")
                        else:
                            show_notification("UEMA Wi-Fi", "Falha no login. Verifique sua senha ou a configuração do sistema.")
                            # Aguarda um tempo maior (2 minutos) se falhar para não ficar em loop bombardeando o servidor
                            time.sleep(120) 
            
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            
        # Espera 10 segundos antes de verificar novamente
        time.sleep(10)

if __name__ == "__main__":
    run_daemon()
