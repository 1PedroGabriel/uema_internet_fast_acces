# Arquitetura e Engenharia de Software - UEMA Fast Access

Este documento sintetiza os padrões de engenharia de software, redes e segurança da informação implementados neste projeto.

---

## 1. Engenharia de Redes & Protocolo do Captive Portal

A identificação de conectividade real e a superação de portais cativos obedecem a uma máquina de estados:

```
[Início] 
   │
   ▼
[Verificar SSID == "UEMA"] ──(Não)──► [Aguarda 15s]
   │ (Sim)
   ▼
[Probe HTTP: msftconnecttest.com] ──(200 OK + 'Microsoft Connect Test')──► [Internet Ativa (Aguarda 20s)]
   │ (Redirecionado ou Bloqueado)
   ▼
[Estabilização DHCP (2s)]
   │
   ▼
[Handshake HTTP com Gateway UEMA]
   │ - Captura de cookies temporários
   │ - Headers: Referer, User-Agent
   ▼
[POST Form Data: user & password] ──► http://172.25.50.10/auth/index.html/u
   │
   ▼
[Pausa de propagação no Firewall (2s)]
   │
   ▼
[Re-teste de Conectividade] ──(Sucesso)──► [Notificação: Conectado]
```

### Por que `msftconnecttest.com`?
Roteadores corporativos de campus universitários interceptam tráfego na porta 80 e aplicam regras de spoofing DNS/HTTP especificamente calibradas para os probes nativos do Windows (`msftconnecttest.com`) e Android (`generate_204`). O uso desse endpoint garante 0% de falsos positivos.

---

## 2. Engenharia de Segurança & SecOps

### Armazenamento Criptográfico Local
A aplicação segue a diretriz de **Zero Plain-Text**:
* **Windows Desktop**: Armazenamento no **Windows Credential Manager (Vault)** através de chamadas nativas do subsistema DPAPI. Mesmo que o arquivo executável seja inspecionado ou descompilado, a chave de descriptografia só é acessível pela sessão autenticada do usuário.
* **Android**: Criptografia em repouso assegurada pelo **Android Keystore**, com chave gerenciada pelo hardware (TEE / StrongBox).
* **iOS**: Chaves salvas na **Keychain** com atributo de acessibilidade restrito ao próprio aplicativo.

### Mitigação de Restrições de Tráfego HTTP Claro (Cleartext Traffic)
Como o gateway `172.25.50.10` opera em HTTP puro dentro da rede local:
* **Android (API 28+)**: Foi adicionada a instrução `android:usesCleartextTraffic="true"` no `AndroidManifest.xml` via automação de build.
* **iOS**: O mecanismo *App Transport Security (ATS)* foi configurado com a chave `NSAllowsArbitraryLoads` no `Info.plist`.

---

## 3. Pipeline de CI/CD (GitHub Actions)

A esteira de integração contínua (`.github/workflows/build_apk.yml`) elimina a necessidade de ferramentas de compilação locais:
* **Scaffolding Dinâmico**: Ao invés de versionar gigabytes de código gerado de Gradle e Xcode no repositório, o GitHub executa `flutter create .` dinamicamente na nuvem.
* **Injeção de Permissões**: Scripts automatizados injetam as permissões de rede nos arquivos de manifesto antes da compilação.
* **Upload Artifacts v4**: Utiliza a versão mais recente e estável do ecossistema GitHub Actions.
