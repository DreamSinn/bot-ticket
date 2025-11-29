# 🚀 Guia de Início Rápido

Este guia mostrará como colocar o bot em funcionamento rapidamente.

## 📋 Passo a Passo

### 1. Criar um Bot no Discord

Acesse o [Portal de Desenvolvedores do Discord](https://discord.com/developers/applications) e siga os passos:

1. Clique em **New Application** e dê um nome ao seu bot.
2. Vá para a aba **Bot** no menu lateral.
3. Clique em **Add Bot** e confirme.
4. Em **Token**, clique em **Copy** para copiar o token do bot (guarde-o em segurança).
5. Ative as seguintes **Privileged Gateway Intents**:
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
6. Vá para a aba **OAuth2** > **URL Generator**.
7. Selecione os seguintes escopos:
   - ✅ `bot`
   - ✅ `applications.commands`
8. Em **Bot Permissions**, selecione:
   - ✅ Manage Channels
   - ✅ Manage Roles
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Manage Messages
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
9. Copie a URL gerada e cole no navegador para adicionar o bot ao seu servidor.

---

### 2. Instalar Dependências

Certifique-se de ter o Python 3.8 ou superior instalado. Em seguida, execute:

```bash
pip install -r requirements.txt
```

---

### 3. Configurar o Arquivo .env

Crie um arquivo chamado `.env` na raiz do projeto e adicione:

```dotenv
DISCORD_TOKEN=SEU_TOKEN_AQUI
GUILD_ID=SEU_SERVER_ID_AQUI
```

**Como obter o ID do servidor?**
1. Ative o **Modo de Desenvolvedor** no Discord (Configurações > Avançado).
2. Clique com o botão direito no ícone do servidor e selecione **Copiar ID do Servidor**.

---

### 4. Executar o Bot

Execute o seguinte comando:

```bash
python src/bot.py
```

Se tudo estiver correto, você verá:

```
Banco de dados inicializado.
Cog carregado: tickets.py
Cog carregado: painel.py
Cog carregado: admin.py
Cog carregado: logs.py
Comandos de barra sincronizados.
------------------------------
Bot conectado como Ticket Bot#1234
ID do Bot: 123456789012345678
Servidor alvo: 987654321098765432
Versão do discord.py: 2.3.2
------------------------------
```

---

### 5. Configurar o Bot no Discord

Use os comandos de configuração no seu servidor:

```
/setup
```

Este comando mostrará um guia completo. Em resumo:

1. **Definir cargo de staff:**
   ```
   /config staff cargo:@Staff
   ```

2. **Definir canal de logs:**
   ```
   /config logs canal:#ticket-logs
   ```

3. **Definir categoria para tickets abertos:**
   ```
   /config categoria-abertos categoria:Tickets
   ```

4. **Criar um painel de tickets:**
   ```
   /painel criar tipo:Simples
   ```

---

### 6. Testar o Sistema

Agora você pode:

- Usar `/ticket` para criar um ticket manualmente.
- Clicar no botão do painel para abrir um ticket.
- Staff pode usar os botões **Claim**, **Disclaim**, **Fechar** e **Deletar** nos tickets.

---

## 🎉 Pronto!

Seu bot de tickets está funcionando! Consulte o arquivo `README.md` para mais detalhes sobre personalização e funcionalidades avançadas.
