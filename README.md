# 🤖 Bot de Tickets Profissional para Discord

Este é um bot de tickets completo e profissional para Discord, desenvolvido em Python com a biblioteca `discord.py`. Ele utiliza **slash commands**, **modals**, **embeds modernos** e um sistema robusto de gerenciamento de tickets, incluindo painéis interativos, sistema de claim/disclaim e logs detalhados.

## 🔥 Funcionalidades Principais

- **Sistema de Tickets via Slash Command**: Crie tickets facilmente com o comando `/ticket`, preenchendo um modal com todas as informações necessárias.
- **Painel Fixo com Botões**: Staff pode instalar painéis fixos em qualquer canal, permitindo que usuários abram tickets com um único clique.
- **Múltiplas Categorias**: Suporte para múltiplas categorias de tickets, configuráveis através de um arquivo `config.json` e painéis específicos.
- **Sistema de Claim/Disclaim**: Staff pode assumir (claim) a responsabilidade por um ticket, evitando que múltiplos moderadores trabalhem no mesmo caso.
- **Logs Profissionais**: Registros detalhados de todas as ações importantes (criação, claim, fechamento, deleção) em um canal de logs dedicado.
- **Transcrições de Tickets**: Ao deletar um ticket, uma transcrição completa da conversa é gerada e enviada para o canal de logs.
- **Anti-Spam**: Impede que usuários criem múltiplos tickets simultaneamente.
- **Comandos de Configuração**: Comandos intuitivos para administradores configurarem cargos de staff, canais de log e categorias de tickets.
- **Arquitetura Modular**: O projeto é organizado em cogs e módulos utilitários, facilitando a manutenção e a expansão.

---

## 📁 Arquitetura do Projeto

O projeto segue uma estrutura modular para garantir organização e escalabilidade:

```
/discord-ticket-bot
├── data/
│   └── tickets.db          # Banco de dados SQLite
├── src/
│   ├── bot.py              # Arquivo principal do bot
│   ├── cogs/               # Módulos de comandos (cogs)
│   │   ├── tickets.py      # Comando /ticket e modal
│   │   ├── painel.py       # Comandos /painel para criar painéis
│   │   ├── admin.py        # Comandos /config para administração
│   │   └── logs.py         # Sistema de logs de eventos
│   └── utils/              # Módulos de utilidades
│       ├── database.py     # Gerenciamento do banco de dados
│       ├── embeds.py       # Construtor de embeds padronizados
│       ├── permissions.py  # Gerenciador de permissões
│       └── ticket_manager.py # Lógica de criação e gerenciamento de tickets
├── .env.example            # Exemplo de arquivo de ambiente
├── config.json             # Configurações de categorias e aparência
└── requirements.txt        # Dependências do projeto
```

---

## ⚙️ Instalação e Configuração

Siga os passos abaixo para hospedar e executar o bot.

### Pré-requisitos

- [Python 3.8+](https://www.python.org/downloads/)
- Um servidor Discord onde você tenha permissões de administrador.
- Um token de bot do [Portal de Desenvolvedores do Discord](https://discord.com/developers/applications).

### 1. Obtenha o Código

Faça o download ou clone este repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd discord-ticket-bot
```

### 2. Instale as Dependências

Crie um ambiente virtual e instale as bibliotecas necessárias:

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure o Ambiente

Renomeie o arquivo `.env.example` para `.env` e preencha as variáveis:

```dotenv
# .env

# Token do seu bot do Discord
DISCORD_TOKEN=seu_token_aqui

# ID do seu servidor (Guild ID)
GUILD_ID=seu_server_id_aqui
```

**Como obter o ID do Servidor?**
1. No Discord, vá em `Configurações de Usuário` > `Avançado`.
2. Ative o `Modo de Desenvolvedor`.
3. Clique com o botão direito no ícone do seu servidor e selecione `Copiar ID do Servidor`.

### 4. Execute o Bot

Inicie o bot com o seguinte comando:

```bash
python src/bot.py
```

Se tudo estiver configurado corretamente, você verá mensagens de confirmação no terminal e o bot ficará online no seu servidor.

---

## 🚀 Comandos de Uso

O bot utiliza slash commands para todas as interações.

### Comandos para Administradores (`/config`)

Use esses comandos para configurar o bot no seu servidor. **Apenas administradores podem usá-los.**

| Comando | Descrição | Exemplo |
| :--- | :--- | :--- |
| `/config staff` | Define o cargo que terá permissões de staff. | `/config staff cargo:@Staff` |
| `/config logs` | Define o canal para onde os logs serão enviados. | `/config logs canal:#ticket-logs` |
| `/config categoria-abertos` | Define a categoria onde os canais de ticket serão criados. | `/config categoria-abertos categoria:Tickets` |
| `/config categoria-fechados` | Define a categoria para onde os tickets fechados são movidos. | `/config categoria-fechados categoria:Arquivo` |
| `/config ver` | Mostra as configurações atuais do bot no servidor. | `/config ver` |
| `/setup` | Mostra um guia rápido de configuração. | `/setup` |

### Comandos para Staff (`/painel`)

| Comando | Descrição | Exemplo |
| :--- | :--- | :--- |
| `/painel criar` | Cria um painel fixo para abrir tickets. | `/painel criar tipo:Simples` |
| `/painel categoria` | Cria um painel para uma categoria específica. | `/painel categoria categoria:Suporte` |

### Comandos para Usuários

| Comando | Descrição |
| :--- | :--- |
| `/ticket` | Abre um modal para criar um novo ticket. |

---

## 🎨 Personalização

Você pode personalizar as categorias de ticket e a aparência do bot editando o arquivo `config.json`:

```json
{
  "bot_name": "Ticket Bot",
  "bot_color": "0x5865F2",
  "categories": {
    "suporte": {
      "name": "Suporte",
      "emoji": "🛠️",
      "description": "Precisa de ajuda técnica ou suporte geral"
    },
    "compras": {
      "name": "Compras",
      "emoji": "🛒",
      "description": "Dúvidas sobre produtos, pagamentos ou pedidos"
    }
  }
}
```

- `bot_name`: Nome que aparece no rodapé dos embeds.
- `bot_color`: Cor principal dos embeds (em formato hexadecimal).
- `categories`: Objeto contendo as categorias de ticket que podem ser usadas nos painéis.
