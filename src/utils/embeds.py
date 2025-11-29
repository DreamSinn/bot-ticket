import discord
from datetime import datetime
from typing import Optional

class EmbedBuilder:
    """Classe para criar embeds padronizados"""
    
    def __init__(self, bot_name: str = "Ticket Bot", color: int = 0x5865F2):
        self.bot_name = bot_name
        self.color = color
    
    def create_ticket_embed(self, user: discord.User, category: str, reason: str, 
                           description: str, urgency: str, claimed_by: Optional[discord.Member] = None) -> discord.Embed:
        """Cria o embed principal do ticket"""
        
        # Define cor baseada na urgência
        urgency_colors = {
            "baixa": 0x00FF00,    # Verde
            "média": 0xFFFF00,    # Amarelo
            "alta": 0xFF0000      # Vermelho
        }
        
        urgency_emojis = {
            "baixa": "🟢",
            "média": "🟡",
            "alta": "🔴"
        }
        
        embed = discord.Embed(
            title=f"📩 Ticket - {category.capitalize()}",
            description=f"**Criado por:** {user.mention}\n**Status:** Aguardando atendimento",
            color=urgency_colors.get(urgency.lower(), self.color),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📝 Motivo",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="📄 Descrição",
            value=description,
            inline=False
        )
        
        embed.add_field(
            name=f"{urgency_emojis.get(urgency.lower(), '⚪')} Urgência",
            value=urgency.capitalize(),
            inline=True
        )
        
        if claimed_by:
            embed.add_field(
                name="👤 Responsável",
                value=claimed_by.mention,
                inline=True
            )
        
        embed.set_footer(
            text=f"{self.bot_name} • Ticket System",
            icon_url=user.display_avatar.url
        )
        
        return embed
    
    def create_panel_embed(self, category: Optional[str] = None, 
                          category_info: Optional[dict] = None) -> discord.Embed:
        """Cria o embed do painel fixo"""
        
        if category and category_info:
            # Painel específico de categoria
            embed = discord.Embed(
                title=f"{category_info.get('emoji', '📩')} {category_info.get('name', 'Ticket')}",
                description=category_info.get('description', 'Clique no botão abaixo para abrir um ticket.'),
                color=self.color,
                timestamp=datetime.utcnow()
            )
        else:
            # Painel geral
            embed = discord.Embed(
                title="📩 Sistema de Tickets",
                description=(
                    "**Bem-vindo ao sistema de suporte!**\n\n"
                    "Clique no botão abaixo para abrir um ticket e nossa equipe "
                    "irá atendê-lo o mais rápido possível.\n\n"
                    "**Como funciona:**\n"
                    "• Clique em **Criar Ticket**\n"
                    "• Preencha as informações solicitadas\n"
                    "• Aguarde o atendimento da equipe\n"
                    "• Seu ticket será criado em um canal privado"
                ),
                color=self.color,
                timestamp=datetime.utcnow()
            )
        
        embed.set_footer(
            text=f"{self.bot_name} • Ticket System",
            icon_url=None
        )
        
        return embed
    
    def create_log_embed(self, action: str, ticket_data: dict, 
                        user: discord.User, **kwargs) -> discord.Embed:
        """Cria embed para logs de ações"""
        
        action_colors = {
            "created": 0x00FF00,
            "claimed": 0x0099FF,
            "disclaimed": 0xFFFF00,
            "closed": 0xFF9900,
            "deleted": 0xFF0000
        }
        
        action_titles = {
            "created": "✅ Ticket Criado",
            "claimed": "👤 Ticket Assumido",
            "disclaimed": "↩️ Ticket Liberado",
            "closed": "🔒 Ticket Fechado",
            "deleted": "🗑️ Ticket Deletado"
        }
        
        embed = discord.Embed(
            title=action_titles.get(action, "📋 Ação no Ticket"),
            color=action_colors.get(action, self.color),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎫 Ticket ID",
            value=f"#{ticket_data.get('ticket_id', 'N/A')}",
            inline=True
        )
        
        embed.add_field(
            name="📂 Categoria",
            value=ticket_data.get('category', 'N/A').capitalize(),
            inline=True
        )
        
        embed.add_field(
            name="👤 Usuário",
            value=user.mention,
            inline=True
        )
        
        if action == "created":
            embed.add_field(
                name="📝 Motivo",
                value=ticket_data.get('reason', 'N/A'),
                inline=False
            )
            embed.add_field(
                name="⚡ Urgência",
                value=ticket_data.get('urgency', 'N/A').capitalize(),
                inline=True
            )
        
        if action == "claimed":
            staff = kwargs.get('staff')
            if staff:
                embed.add_field(
                    name="🛡️ Staff Responsável",
                    value=staff.mention,
                    inline=False
                )
        
        if action in ["closed", "deleted"]:
            reason = kwargs.get('reason')
            if reason:
                embed.add_field(
                    name="📄 Motivo",
                    value=reason,
                    inline=False
                )
            
            created_at = ticket_data.get('created_at')
            if created_at:
                try:
                    created = datetime.fromisoformat(created_at)
                    duration = datetime.utcnow() - created
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    
                    embed.add_field(
                        name="⏱️ Tempo Aberto",
                        value=f"{hours}h {minutes}m",
                        inline=True
                    )
                except:
                    pass
        
        embed.set_footer(
            text=f"{self.bot_name} • Log System"
        )
        
        return embed
    
    def create_error_embed(self, title: str, description: str) -> discord.Embed:
        """Cria embed de erro"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=0xFF0000,
            timestamp=datetime.utcnow()
        )
        return embed
    
    def create_success_embed(self, title: str, description: str) -> discord.Embed:
        """Cria embed de sucesso"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        return embed
    
    def create_info_embed(self, title: str, description: str) -> discord.Embed:
        """Cria embed informativo"""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=self.color,
            timestamp=datetime.utcnow()
        )
        return embed
