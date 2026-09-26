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
[Descoberta Dinâmica do Portal]
   │ - Segue redirect do probe
   │ - Extrai 'action' do formulário HTML
   │ - Valida: HTTP + IP privado (anti-phishing)
   │ - Fallback: 172.25.50.10/auth/index.html/u
   ▼
[POST Form Data: user & password] ──► URL descoberta dinamicamente
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
Como o portal cativo da UEMA opera em HTTP puro dentro da rede local:
* **Android (API 28+)**: `network_security_config.xml` versionado libera cleartext **somente** para `172.25.50.10` e `msftconnecttest.com`; todo o restante exige TLS.
* **iOS**: App Transport Security configurado com `NSExceptionDomains` restrito aos mesmos destinos (não usa `NSAllowsArbitraryLoads`).

### Faixas de IP Observadas na Rede UEMA
O cliente Wi-Fi recebe IP da faixa `10.x.x.x` (observado `10.101.x.x`) enquanto o controlador do portal usa `172.25.x.x`. Por isso a validação anti-vazamento aceita qualquer faixa privada (RFC1918) no cliente e valida o destino do portal separadamente.

---

## 3. Pipeline de CI/CD (GitHub Actions)

A esteira de integração contínua (`.github/workflows/build_apk.yml`) elimina a necessidade de ferramentas de compilação locais:
* **Scaffolding Dinâmico**: Ao invés de versionar gigabytes de código gerado de Gradle e Xcode no repositório, o GitHub executa `flutter create .` dinamicamente na nuvem.
* **Injeção de Permissões**: Scripts automatizados injetam as permissões de rede nos arquivos de manifesto antes da compilação.
* **Upload Artifacts v4**: Utiliza a versão mais recente e estável do ecossistema GitHub Actions.
