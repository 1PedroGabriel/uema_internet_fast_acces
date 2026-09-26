# UEMA Internet Fast Access 🚀

Solução automatizada, segura e multiplataforma para autenticação em segundo plano na rede Wi-Fi da Universidade Estadual do Maranhão (UEMA).

Resolve de vez a desconexão repetitiva que ocorre ao circular entre blocos e prédios do campus.

---

## 💻 1. Versão Computador (Windows .exe)

A versão Desktop roda de forma invisível em segundo plano e inclui persistência automática no sistema operacional.

### Como Funciona:
1. **Identificação de Rede**: Monitora ativamente o SSID da rede `UEMA`.
2. **Teste de Conectividade**: Valida o acesso através do endpoint oficial de probe (`msftconnecttest.com`).
3. **Autenticação Automática**: Se o captive portal interceptar o tráfego, o app faz o handshake, envia os cabeçalhos (`Referer`) e submete as credenciais do SIGUEMA diretamente ao gateway `http://172.25.50.10/auth/index.html/u`.
4. **Primeiro Uso**: Se as credenciais não estiverem cadastradas, exibe uma interface gráfica simples solicitando Matrícula e Senha.
5. **Persistência**: Opção de iniciar automaticamente junto com o Windows (sem precisar abrir o app manualmente).

### Como Gerar o Executável:
Na pasta `desktop_app`:
```powershell
python build.py
```
O executável final pronto para uso e distribuição será gerado em: `desktop_app/dist/UEMA_Internet_FastAccess.exe`.

---

## 📱 2. Versão Celular (Android & iOS)

Desenvolvida em Flutter para entregar binários nativos para smartphones.

### Estratégia de Uso:
Devido às políticas rígidas de economia de bateria do Android e iOS contra requisições em segundo plano, o aplicativo adota o fluxo **"1-Tap Connect"**:
* O aluno cadastra o acesso uma única vez.
* Ao chegar na UEMA ou trocar de bloco, basta tocar no botão **"1-Tap Connect"** para que a internet seja liberada instantaneamente em 1 segundo.

### Como Baixar os Executáveis Mobile (CI/CD Automático):
Você **não** precisa de Android Studio ou Xcode instalados localmente.
1. Ao enviar o código para o GitHub, a esteira do **GitHub Actions** compila os aplicativos na nuvem.
2. Acesse a aba **Actions** no seu repositório do GitHub.
3. Clique na última execução da esteira e baixe:
   * 🟢 **UEMA_FastAccess_Android_APK** (Arquivo `.apk` para instalar diretamente no Android).
   * 🍎 **UEMA_FastAccess_iOS_APP** (Pacote `.zip` para instalação no iOS via AltStore / Sideloadly).

---

## 🔒 Segurança e Armazenamento

* **Zero Plain-Text**: Senhas **nunca** são salvas em arquivos de texto ou banco local desprotegido.
  * **No Windows**: Utiliza o **Windows Credential Locker (Vault)** via DPAPI.
  * **No Android**: Criptografia por hardware via **Android Keystore** (`EncryptedSharedPreferences`).
  * **No iOS**: Criptografia segura via **Apple Keychain**.
* **Tráfego Local**: Comunicação direcionada unicamente para o IP interno do gateway da universidade (`172.25.50.10`).
