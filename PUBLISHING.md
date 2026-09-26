# Guia de Publicação — Google Play Store

Este documento descreve como publicar o UEMA FastAccess na Play Store, tornando a instalação mais segura (sem avisos de "fonte desconhecida") e com atualizações automáticas para os usuários.

---

## 1. Custos e requisitos da conta

| Item | Detalhe |
|---|---|
| Taxa | **US$ 25** (pagamento único) em [play.google.com/console](https://play.google.com/console) |
| Identidade | Verificação com documento oficial (RG/CNH/passaporte) |
| Contas pessoais novas | Google exige **teste fechado com 12 testadores por 14 dias** antes de liberar produção |
| Política de privacidade | Obrigatória (app lida com credenciais) — já disponível em `docs/privacidade.html` (publicada pelo GitHub Pages) |

---

## 2. Gerar a chave de assinatura (uma vez só)

No seu computador, com o Java instalado:

```powershell
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias uema-fastaccess
```

**Guarde esse arquivo e as senhas em local seguro.** Se perder a chave, nunca mais conseguirá atualizar o app na loja (a não ser que ative o Play App Signing, recomendado no passo 5).

## 3. Configurar os secrets no GitHub

Gere a versão Base64 do keystore:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("upload-keystore.jks")) | Set-Clipboard
```

Depois, em **Settings → Secrets and variables → Actions → New repository secret**, crie:

| Secret | Valor |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | Base64 copiado acima |
| `KEYSTORE_PASSWORD` | Senha do keystore |
| `KEY_PASSWORD` | Senha da chave |
| `KEY_ALIAS` | `uema-fastaccess` |

Com os secrets presentes, a esteira passa a **assinar o AAB automaticamente** a cada tag.

## 4. Gerar o AAB assinado

```powershell
git tag v1.1.0
git push origin v1.1.0
```

Baixe o artifact **UEMA_FastAccess_Android_AAB** na aba Actions. O `app-release.aab` é o arquivo que vai para o Play Console.

## 5. Criar o app no Play Console

1. **Criar app** → nome: **FastAccess** (já aplicado no código). Não use "UEMA" como nome principal — a marca pertence à universidade e o Google rejeita por *impersonação*. Descreva na ficha como "compatível com a rede Wi-Fi da UEMA".
2. **Play App Signing**: ative (recomendado) — o Google guarda a chave principal e sua chave local vira apenas a "chave de upload".
3. **Ficha da loja**: descrição curta/longa, ícone 512×512, imagem de destaque 1024×500 e 2+ capturas de tela do app.
4. **Política de privacidade**: aponte para `https://1pedrogabriel.github.io/uema_internet_fast_acces/privacidade.html`.
5. **Data Safety (Segurança dos dados)**:
   - Coleta dados? **Sim** → Credenciais de autenticação
   - Compartilhados com terceiros? **Não**
   - Criptografados em trânsito? **Não** (seja honesto: o portal da UEMA é HTTP — declare isso; o formulário tem campo para explicar)
   - Dados apagáveis pelo usuário? **Sim**
6. **Classificação de conteúdo**: questionário padrão (app utilitário, sem conteúdo sensível).
7. **Teste fechado**: crie uma lista com 12 e-mails de testadores (colegas) e aguarde o período exigido de 14 dias antes de pedir produção.

## 6. Por que a Play Store é mais segura para os usuários

- Sem aviso de "fonte desconhecida" nem retenção do download em 100%;
- Play Protect valida a assinatura e integridade do app;
- **Atualizações automáticas** — correções de segurança chegam sem depender do usuário visitar o site;
- A política de privacidade e o formulário Data Safety ficam públicos na página do app.

## 7. Manutenção contínua

- A cada correção: suba uma tag `v*` nova. A esteira gera AAB assinado; faça upload no Play Console como nova versão (o `versionCode` é incrementado automaticamente a partir do número da execução).
- O Google exige que novos apps mirem o nível de API Android recente; por isso a esteira usa o canal `stable` mais recente do Flutter.
- O download direto (ZIP no site) continua disponível como alternativa.
