# Arquitetura e Engenharia de Software - UEMA Fast Access

Este documento descreve as decisões de engenharia de software e arquitetura de redes tomadas no desenvolvimento deste utilitário. O objetivo do sistema é automatizar a autenticação em *Captive Portals* (redes Wi-Fi que exigem login web) de forma segura, silenciosa e multiplataforma.

## 1. Engenharia de Redes: Detecção de Captive Portal

A identificação de se o dispositivo tem acesso livre à internet ou se está "sequestrado" pelo portal da universidade utiliza o mesmo padrão adotado globalmente pelos sistemas operacionais Android, ChromeOS e iOS.

*   **O Endpoint de Teste:** O sistema envia uma requisição `GET` para `http://clients3.google.com/generate_204`.
*   **A Lógica do HTTP 204:**
    *   **HTTP 204 (No Content):** Se o roteador permitir que o pacote vá até os servidores do Google e volte, o Google responde com um cabeçalho 204. Isso significa: **Internet livre.**
    *   **HTTP 200 / 302:** Se a rede Wi-Fi interceptar o tráfego (o comportamento padrão de roteadores de universidades/aeroportos), ela redirecionará a requisição HTTP do usuário para a página de login interna. Como a requisição foi redirecionada, a resposta final será um HTTP 200 (OK).
    *   **Decisão Algorítmica:** Se `statusCode != 204`, o algoritmo sabe que precisa agir e injetar as credenciais.

## 2. Arquitetura de Segurança (SecOps)

Manipular senhas de acesso à rede institucional exige rigor. A aplicação adota as seguintes premissas de segurança:

### Mitigação de Ataques *Man-in-the-Middle* (Evil Twin)
Redes Wi-Fi abertas são vulneráveis a ataques *Evil Twin*, onde um atacante cria um Wi-Fi falso com o mesmo nome (SSID) da UEMA para capturar senhas em texto plano.
*   **Solução:** O POST de autenticação é disparado **estritamente via HTTPS**, com a *flag* `verify=True` nas bibliotecas de rede. Se o roteador não possuir o certificado SSL/TLS oficial e válido da UEMA, a aplicação aborta a conexão para proteger o usuário.

### Armazenamento de Credenciais (Zero Plain-Text)
Arquivos `.txt`, `.json` ou bancos de dados SQLite locais são inaceitáveis para armazenamento de senhas, pois qualquer malware básico pode lê-los.
*   **Desktop (Python):** Utiliza-se a API `keyring`, que interage diretamente com o **Gerenciador de Credenciais do Windows (Credential Locker)**, a **Keychain do macOS** e o **Secret Service do Linux**. A chave criptográfica pertence ao usuário do SO.
*   **Mobile (Flutter):** Utiliza-se o pacote `flutter_secure_storage`, que faz a ponte direta com o hardware nativo: **Android Keystore System** (cifrado por hardware via TEE/SE) e o **iOS Keychain**.

## 3. Pipeline de CI/CD (GitHub Actions)

Para garantir que o código fonte se transforme de maneira reprodutível em artefatos binários seguros, foi implementada uma esteira de Continuous Integration no GitHub Actions.

*   **Gatilho:** Qualquer _Push_ ou _Pull Request_ na branch `main`.
*   **Jobs Simultâneos:**
    *   `build-android`: Roda em ambiente Ubuntu. Instala a SDK do Flutter, gerencia dependências e compila um artefato `.apk` em modo `--release` (com código otimizado em Dart AOT).
    *   `build-ios`: Roda em ambiente macOS. Compila o binário iOS nativo (`.app`), compactando-o e disponibilizando o `.zip`.
*   **Vantagem Arquitetural:** O desenvolvedor não precisa manter SDKs pesadas na máquina local. O GitHub atua como o *Build Server* oficial da aplicação, garantindo transparência no executável gerado.
