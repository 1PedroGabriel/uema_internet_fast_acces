# FastAccess — Wi-Fi UEMA 🚀

> Aplicativo **independente e sem vínculo oficial** com a UEMA. "UEMA" é citado apenas para identificar a rede compatível.

Solução automatizada, segura e multiplataforma para autenticação em segundo plano na rede Wi-Fi da Universidade Estadual do Maranhão (UEMA).

Resolve de vez a desconexão repetitiva que ocorre ao circular entre blocos e prédios do campus.

---

## 💻 1. Versão Computador (Windows .exe)

A versão Desktop roda de forma invisível em segundo plano e inclui persistência automática no sistema operacional.

### Como Funciona:
1. **Identificação de Rede**: Monitora ativamente o SSID da rede `UEMA` (correspondência exata, case-insensitive).
2. **Teste de Conectividade**: Valida o acesso através do endpoint oficial de probe (`msftconnecttest.com`).
3. **Descoberta Dinâmica do Portal**: Ao detectar o captive portal, o app segue o redirecionamento e extrai a URL real de autenticação do formulário — funciona mesmo se o endereço do controlador mudar entre campi. Só aceita destino HTTP em IP privado (anti-phishing).
4. **Autenticação Automática**: Envia os cabeçalhos (`Referer`) e submete as credenciais do SIGUEMA ao gateway descoberto (fallback: `http://172.25.50.10/auth/index.html/u`).
5. **Primeiro Uso**: Se as credenciais não estiverem cadastradas, abre uma janela de configuração em processo separado (sem travar o daemon).
6. **Auto-recuperação de Senha**: Se o portal rejeitar as credenciais em dois ciclos consecutivos (senha trocada no SIGUEMA), a senha é removida do cofre e a janela de recadastro abre automaticamente.
7. **Persistência**: Opção de iniciar automaticamente junto com o Windows (sem precisar abrir o app manualmente).

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
* **Tráfego Local Restrito**: Comunicação direcionada apenas para IPs privados da rede da universidade; cleartext HTTP permitido somente ao portal e ao probe (via `networkSecurityConfig` no Android e `NSExceptionDomains` no iOS).
* **Descoberta Dinâmica com Validação**: O endereço do portal é descoberto a cada conexão e rejeitado se não for HTTP em IP privado.
* **⚠ Limitação Inerente ao Portal**: O gateway da UEMA aceita credenciais por HTTP sem TLS. O app mitiga com validação de rede e anti-phishing, mas **não pode proteger a senha em trânsito** — isso depende da CTIC/PROINFRA habilitar HTTPS ou 802.1X.
