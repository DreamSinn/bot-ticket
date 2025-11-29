import discord
from discord.ext import commands
from datetime import datetime

class LogsCog(commands.Cog):
    """Cog para sistema de logs profissionais"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.embed_builder = bot.embed_builder
    
    async def send_log(self, guild: discord.Guild, embed: discord.Embed, file: discord.File = None):
        """Envia um log para o canal de logs configurado"""
        config = await self.db.get_guild_config(guild.id)
        
        if config and config.get("log_channel_id"):
            log_channel = guild.get_channel(config["log_channel_id"])
            if log_channel:
                try:
                    if file:
                        await log_channel.send(embed=embed, file=file)
                    else:
                        await log_channel.send(embed=embed)
                except Exception as e:
                    print(f"Erro ao enviar log: {e}")
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        """Detecta quando um canal de ticket é deletado manualmente"""
        # Verifica se era um canal de ticket
        ticket_data = await self.db.get_ticket_by_channel(channel.id)
        
        if ticket_data and ticket_data['status'] == 'open':
            # Canal foi deletado sem usar o sistema
            user = channel.guild.get_member(ticket_data['user_id'])
            
            embed = discord.Embed(
                title="⚠️ Ticket Deletado Manualmente",
                description=f"Um canal de ticket foi deletado fora do sistema.",
                color=0xFF9900,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🎫 Ticket ID",
                value=f"#{ticket_data['ticket_id']}",
                inline=True
            )
            
            embed.add_field(
                name="📂 Categoria",
                value=ticket_data['category'].capitalize(),
                inline=True
            )
            
            if user:
                embed.add_field(
                    name="👤 Usuário",
                    value=user.mention,
                    inline=True
                )
            
            embed.add_field(
                name="📝 Motivo",
                value=ticket_data['reason'],
                inline=False
            )
            
            embed.set_footer(text=f"{self.embed_builder.bot_name} • Log System")
            
            await self.send_log(channel.guild, embed)
            
            # Atualiza status no banco
            await self.db.close_ticket(channel.id, "Deletado manualmente")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Registra mensagens em canais de ticket para estatísticas"""
        # Ignora mensagens do bot
        if message.author.bot:
            return
        
        # Ignora DMs
        if not message.guild:
            return
        
        # Verifica se é um canal de ticket
        ticket_data = await self.db.get_ticket_by_channel(message.channel.id)
        
        if ticket_data:
            # Registra atividade (pode ser usado para métricas de tempo de resposta)
            # Por enquanto, apenas registramos no log do ticket
            await self.db.add_log(
                ticket_id=ticket_data['ticket_id'],
                user_id=message.author.id,
                action="message",
                details=f"Mensagem enviada: {len(message.content)} caracteres"
            )


async def setup(bot):
    await bot.add_cog(LogsCog(bot))
