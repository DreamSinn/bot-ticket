import discord
from discord import app_commands
from discord.ext import commands
import json

class TicketModal(discord.ui.Modal, title="Criar Ticket"):
    """Modal para criação de ticket"""
    
    def __init__(self, bot, db, embed_builder, permission_manager, ticket_manager, category: str = None):
        super().__init__()
        self.bot = bot
        self.db = db
        self.embed_builder = embed_builder
        self.permission_manager = permission_manager
        self.ticket_manager = ticket_manager
        self.selected_category = category
        
        # Se não houver categoria pré-selecionada, adiciona campo de categoria
        if not category:
            self.category_field = discord.ui.TextInput(
                label="Categoria",
                placeholder="suporte, compras, denúncia, parcerias, customizado",
                required=True,
                max_length=50
            )
            self.add_item(self.category_field)
    
    reason = discord.ui.TextInput(
        label="Motivo do Ticket",
        placeholder="Descreva brevemente o motivo do seu ticket",
        required=True,
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label="Descrição Detalhada",
        placeholder="Forneça mais detalhes sobre sua solicitação",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    urgency = discord.ui.TextInput(
        label="Nível de Urgência",
        placeholder="baixa, média ou alta",
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # Obtém a categoria
        if self.selected_category:
            category = self.selected_category
        else:
            category = str(self.category_field.value).lower().strip()
        
        reason = str(self.reason.value)
        description = str(self.description.value)
        urgency = str(self.urgency.value).lower().strip()
        
        # Valida urgência
        if urgency not in ["baixa", "média", "alta"]:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Urgência Inválida",
                    "Por favor, escolha entre: **baixa**, **média** ou **alta**"
                ),
                ephemeral=True
            )
            return
        
        # Verifica se usuário já tem ticket aberto (anti-spam)
        open_tickets = await self.db.get_user_open_tickets(interaction.guild.id, interaction.user.id)
        if open_tickets:
            ticket_mentions = ", ".join([f"<#{t['channel_id']}>" for t in open_tickets])
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Ticket Já Existe",
                    f"Você já possui ticket(s) aberto(s): {ticket_mentions}\n\n"
                    f"Por favor, aguarde o atendimento ou feche seus tickets atuais antes de abrir um novo."
                ),
                ephemeral=True
            )
            return
        
        # Responde imediatamente para evitar timeout
        await interaction.response.send_message(
            embed=self.embed_builder.create_info_embed(
                "Criando Ticket",
                "⏳ Aguarde, seu ticket está sendo criado..."
            ),
            ephemeral=True
        )
        
        # Cria o canal do ticket
        channel = await self.ticket_manager.create_ticket_channel(
            guild=interaction.guild,
            user=interaction.user,
            category_name=category,
            reason=reason,
            description=description,
            urgency=urgency
        )
        
        if channel:
            # Envia mensagem inicial no ticket
            await self.ticket_manager.send_ticket_message(
                channel=channel,
                user=interaction.user,
                category=category,
                reason=reason,
                description=description,
                urgency=urgency
            )
            
            # Envia log para canal de logs
            ticket_data = await self.db.get_ticket_by_channel(channel.id)
            if ticket_data:
                config = await self.db.get_guild_config(interaction.guild.id)
                if config and config.get("log_channel_id"):
                    log_channel = interaction.guild.get_channel(config["log_channel_id"])
                    if log_channel:
                        log_embed = self.embed_builder.create_log_embed(
                            action="created",
                            ticket_data=ticket_data,
                            user=interaction.user
                        )
                        await log_channel.send(embed=log_embed)
            
            # Atualiza mensagem de confirmação
            await interaction.edit_original_response(
                embed=self.embed_builder.create_success_embed(
                    "Ticket Criado!",
                    f"Seu ticket foi criado com sucesso!\n\n"
                    f"📍 Canal: {channel.mention}\n"
                    f"📂 Categoria: {category.capitalize()}\n\n"
                    f"Nossa equipe será notificada e irá atendê-lo em breve."
                )
            )
        else:
            await interaction.edit_original_response(
                embed=self.embed_builder.create_error_embed(
                    "Erro ao Criar Ticket",
                    "Ocorreu um erro ao criar seu ticket. Por favor, tente novamente ou contate um administrador."
                )
            )


class TicketsCog(commands.Cog):
    """Cog principal de gerenciamento de tickets"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.embed_builder = bot.embed_builder
        self.permission_manager = bot.permission_manager
        self.ticket_manager = bot.ticket_manager
    
    @app_commands.command(name="ticket", description="Abre um ticket de suporte")
    async def ticket_command(self, interaction: discord.Interaction):
        """Comando /ticket para usuários"""
        
        # Abre o modal
        modal = TicketModal(
            self.bot,
            self.db,
            self.embed_builder,
            self.permission_manager,
            self.ticket_manager
        )
        
        await interaction.response.send_modal(modal)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Registra views persistentes quando o bot inicia"""
        from utils.ticket_manager import TicketControlView
        
        # Registra a view de controle de tickets
        self.bot.add_view(TicketControlView(
            self.bot,
            self.db,
            self.embed_builder,
            self.permission_manager
        ))


async def setup(bot):
    await bot.add_cog(TicketsCog(bot))
