# UEMA Internet Fast Access

Este projeto visa resolver um problema comum em ambientes universitários: a necessidade de fazer login repetidas vezes no portal Wi-Fi (Captive Portal) sempre que você troca de prédio ou a sessão expira.

O aplicativo funciona em *background* (segundo plano). O fluxo principal é:
1. **Estou na internet da UEMA?** (Verifica o SSID do Wi-Fi).
2. **Estou logado?** (Faz um ping seguro para checar se a internet está liberada ou retida no portal).
3. **Use credenciais registradas**: Recupera as credenciais criptografadas de forma automática.
4. **Primeiro uso**: Se as credenciais não existirem, abre uma janela pedindo para o usuário se registrar.

## Foco em Segurança 🔒

Este aplicativo **NÃO** salva senhas em arquivos de texto (txt/json/sqlite). Ele utiliza a biblioteca `keyring` do Python, que armazena os dados de forma criptografada nos cofres nativos do Sistema Operacional:
* **Windows**: Gerenciador de Credenciais do Windows (Credential Locker).
* **macOS**: Keychain.
* **Linux**: Secret Service (KWallet / GNOME Keyring).

Além disso, a requisição de login utiliza `verify=True` para garantir validação do Certificado SSL, protegendo contra redes Wi-Fi falsas (*Evil Twin attacks*).

---

## 🛠️ Como configurar (Para o Desenvolvedor)

Como os portais de internet de cada universidade têm links diferentes, você precisará configurar a URL exata do portal da UEMA antes de gerar o `.exe`.

1. Conecte-se na Wi-Fi da UEMA.
2. Quando a tela de login abrir no navegador, aperte **F12** e vá na aba **Network (Rede)**.
3. Preencha seu usuário e senha e clique em Entrar.
4. Na aba Network, procure a primeira requisição do tipo **POST**.
5. Clique nela e veja os parâmetros:
   * **URL**: Qual é o link que recebeu o POST?
   * **Payload/Form Data**: Quais são os nomes dos campos (ex: `username`, `password`, `user`, `pass`)?
6. Abra o arquivo `desktop_app/network.py` e altere as constantes `LOGIN_URL`, `USER_FIELD` e `PASS_FIELD` com os dados que você encontrou.

---

## 🚀 Como gerar o Executável (.exe) para as pessoas baixarem

Basta ter o Python instalado em seu computador. Na pasta do projeto (`desktop_app`), execute:

```bash
python build.py
```

Isso irá baixar as dependências automaticamente e criar uma pasta chamada `dist`. Lá dentro, estará o arquivo **UEMA_Internet_FastAccess.exe**.

A pessoa (usuário final) só precisa baixar esse arquivo e colocá-lo para rodar junto com a inicialização do Windows.

---

## 📱 E o aplicativo para Celular (Mobile)?

Dispositivos móveis (Android/iOS) possuem sistemas operacionais extremamente restritos quanto à execução de tarefas de rede em background para economizar bateria. Além disso, o próprio celular intercepta captive portals antes que os apps comuns o façam.

Para criar a versão mobile deste app e publicar no GitHub, a arquitetura recomendada é usar **Flutter** ou **React Native** com os seguintes recursos nativos:

### Arquitetura Android (Kotlin/Flutter):
1. **Armazenamento Seguro**: Use `EncryptedSharedPreferences` (Android) ou `flutter_secure_storage`.
2. **Foreground Service / WorkManager**: Para o Android permitir que seu app monitore a rede no fundo, você precisará de um *Foreground Service* (que deixa uma notificação permanente) ou registrar um `ConnectivityManager.NetworkCallback` que é acionado quando a rede Wi-Fi muda.
3. **Captive Portal Bypass**: O app envia um HTTP POST silencioso para a mesma `LOGIN_URL` usando a biblioteca de HTTP do celular no momento em que detecta o SSID "UEMA-WIFI".

Você pode hospedar ambas as versões no GitHub: a versão Desktop (em Python) e o código fonte da versão Mobile (Flutter), disponibilizando o `.exe` e o `.apk` na aba **Releases** do seu repositório.
