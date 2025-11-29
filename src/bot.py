import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

# Importar utilitários
from utils.database import Database
from utils.embeds import EmbedBuilder
from utils.permissions import PermissionManager
from utils.ticket_manager import TicketManager

# Carregar configurações
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

class TicketBot(commands.Bot):
    """Classe principal do bot"""
    
    def __init__(self, guild_id: int):
        # Definir intents (permissões) do bot
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True
        
        super().__init__(command_prefix="!", intents=intents)
        
        self.guild_id = guild_id
        
        # Inicializar utilitários
        self.db = Database()
        self.embed_builder = EmbedBuilder(
            bot_name=config.get("bot_name", "Ticket Bot"),
            color=int(config.get("bot_color", "0x5865F2"), 16)
        )
        self.permission_manager = PermissionManager(self.db)
        self.ticket_manager = TicketManager(self, self.db, self.embed_builder, self.permission_manager)

    async def setup_hook(self):
        """Função executada quando o bot está pronto para iniciar"""
        
        # Inicializar o banco de dados
        await self.db.init_db()
        print("Banco de dados inicializado.")
        
        # Carregar cogs
        for filename in os.listdir("./src/cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Cog carregado: {filename}")
                except Exception as e:
                    print(f"Erro ao carregar cog {filename}: {e}")
        
        # Sincronizar comandos de barra (slash commands)
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Comandos de barra sincronizados.")

    async def on_ready(self):
        """Evento executado quando o bot está online e pronto"""
        print("-" * 30)
        print(f"Bot conectado como {self.user}")
        print(f"ID do Bot: {self.user.id}")
        print(f"Servidor alvo: {self.guild_id}")
        print(f"Versão do discord.py: {discord.__version__}")
        print("-" * 30)
        
        # Define a presença do bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"o servidor com {self.user.name}"
            )
        )

if __name__ == "__main__":
    # Obter token e ID do servidor do .env
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD_ID = os.getenv("GUILD_ID")
    
    if not DISCORD_TOKEN or not GUILD_ID:
        print("Erro: DISCORD_TOKEN e GUILD_ID devem ser definidos no arquivo .env")
    else:
        try:
            # Criar e executar o bot
            bot = TicketBot(guild_id=int(GUILD_ID))
            bot.run(DISCORD_TOKEN)
        except ValueError:
            print("Erro: GUILD_ID deve ser um número inteiro.")
        except Exception as e:
            print(f"Ocorreu um erro ao iniciar o bot: {e}")
