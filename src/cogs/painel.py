import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import json

class PanelButtonView(discord.ui.View):
    """View com botão para criar ticket do painel"""
    
    def __init__(self, bot, category: str = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.category = category
    
    @discord.ui.button(
        label="📩 Criar Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="panel_create_ticket"
    )
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para criar ticket via painel"""
        from cogs.tickets import TicketModal
        
        # Abre o modal (igual ao comando /ticket)
        modal = TicketModal(
            self.bot,
            self.bot.db,
            self.bot.embed_builder,
            self.bot.permission_manager,
            self.bot.ticket_manager,
            category=self.category
        )
        
        await interaction.response.send_modal(modal)


class CategorySelectView(discord.ui.View):
    """View com select menu para escolher categoria"""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # Carrega categorias do config
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        categories = config.get("categories", {})
        
        # Cria opções do select menu
        options = []
        for key, cat_info in categories.items():
            options.append(
                discord.SelectOption(
                    label=cat_info.get("name", key.capitalize()),
                    value=key,
                    description=cat_info.get("description", "")[:100],
                    emoji=cat_info.get("emoji", "📝")
                )
            )
        
        # Adiciona o select menu
        self.category_select = discord.ui.Select(
            placeholder="Selecione a categoria do seu ticket",
            options=options,
            custom_id="panel_category_select"
        )
        self.category_select.callback = self.select_callback
        self.add_item(self.category_select)
    
    async def select_callback(self, interaction: discord.Interaction):
        """Callback quando uma categoria é selecionada"""
        from cogs.tickets import TicketModal
        
        selected_category = self.category_select.values[0]
        
        # Abre o modal com a categoria pré-selecionada
        modal = TicketModal(
            self.bot,
            self.bot.db,
            self.bot.embed_builder,
            self.bot.permission_manager,
            self.bot.ticket_manager,
            category=selected_category
        )
        
        await interaction.response.send_modal(modal)


class PainelCog(commands.Cog):
    """Cog para gerenciamento de painéis fixos"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.embed_builder = bot.embed_builder
        self.permission_manager = bot.permission_manager
    
    painel_group = app_commands.Group(
        name="painel",
        description="Comandos de gerenciamento de painéis de tickets"
    )
    
    @painel_group.command(name="criar", description="Cria um painel fixo de tickets")
    @app_commands.describe(
        canal="Canal onde o painel será enviado (opcional, padrão: canal atual)",
        tipo="Tipo de painel: simples (um botão) ou categorias (menu de seleção)"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Simples (um botão)", value="simple"),
        app_commands.Choice(name="Com Categorias (menu)", value="categories")
    ])
    async def painel_criar(
        self,
        interaction: discord.Interaction,
        tipo: app_commands.Choice[str],
        canal: Optional[discord.TextChannel] = None
    ):
        """Cria um painel fixo de tickets"""
        
        # Verifica se é staff
        if not await self.permission_manager.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas membros da equipe podem criar painéis."
                ),
                ephemeral=True
            )
            return
        
        # Define o canal
        target_channel = canal or interaction.channel
        
        # Verifica permissões no canal
        if not target_channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    f"Não tenho permissão para enviar mensagens em {target_channel.mention}"
                ),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            if tipo.value == "simple":
                # Painel simples com um botão
                embed = self.embed_builder.create_panel_embed()
                view = PanelButtonView(self.bot)
                
                message = await target_channel.send(embed=embed, view=view)
                
            else:  # categories
                # Painel com menu de categorias
                embed = discord.Embed(
                    title="📩 Sistema de Tickets - Escolha a Categoria",
                    description=(
                        "**Bem-vindo ao sistema de suporte!**\n\n"
                        "Selecione abaixo a categoria que melhor descreve seu ticket.\n"
                        "Após selecionar, você preencherá um formulário com mais detalhes."
                    ),
                    color=self.embed_builder.color,
                    timestamp=discord.utils.utcnow()
                )
                
                embed.set_footer(text=f"{self.embed_builder.bot_name} • Ticket System")
                
                view = CategorySelectView(self.bot)
                
                message = await target_channel.send(embed=embed, view=view)
            
            # Registra o painel no banco de dados
            await self.db.create_panel(
                guild_id=interaction.guild.id,
                channel_id=target_channel.id,
                message_id=message.id,
                panel_type=tipo.value
            )
            
            await interaction.followup.send(
                embed=self.embed_builder.create_success_embed(
                    "Painel Criado!",
                    f"O painel de tickets foi criado com sucesso em {target_channel.mention}\n"
                    f"**Tipo:** {tipo.name}\n"
                    f"**Link:** [Clique aqui]({message.jump_url})"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                embed=self.embed_builder.create_error_embed(
                    "Erro ao Criar Painel",
                    f"Ocorreu um erro: {str(e)}"
                ),
                ephemeral=True
            )
    
    @painel_group.command(name="categoria", description="Cria um painel para uma categoria específica")
    @app_commands.describe(
        categoria="Categoria do painel",
        canal="Canal onde o painel será enviado (opcional, padrão: canal atual)"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name="🛠️ Suporte", value="suporte"),
        app_commands.Choice(name="🛒 Compras", value="compras"),
        app_commands.Choice(name="⚠️ Denúncia", value="denuncia"),
        app_commands.Choice(name="🤝 Parcerias", value="parcerias"),
        app_commands.Choice(name="📝 Customizado", value="customizado")
    ])
    async def painel_categoria(
        self,
        interaction: discord.Interaction,
        categoria: app_commands.Choice[str],
        canal: Optional[discord.TextChannel] = None
    ):
        """Cria um painel fixo para uma categoria específica"""
        
        # Verifica se é staff
        if not await self.permission_manager.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas membros da equipe podem criar painéis."
                ),
                ephemeral=True
            )
            return
        
        # Define o canal
        target_channel = canal or interaction.channel
        
        # Verifica permissões no canal
        if not target_channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    f"Não tenho permissão para enviar mensagens em {target_channel.mention}"
                ),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Carrega informações da categoria
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            category_info = config.get("categories", {}).get(categoria.value, {})
            
            # Cria embed específico da categoria
            embed = self.embed_builder.create_panel_embed(
                category=categoria.value,
                category_info=category_info
            )
            
            # Cria view com botão
            view = PanelButtonView(self.bot, category=categoria.value)
            
            # Envia o painel
            message = await target_channel.send(embed=embed, view=view)
            
            # Registra no banco de dados
            await self.db.create_panel(
                guild_id=interaction.guild.id,
                channel_id=target_channel.id,
                message_id=message.id,
                panel_type=f"category_{categoria.value}"
            )
            
            await interaction.followup.send(
                embed=self.embed_builder.create_success_embed(
                    "Painel de Categoria Criado!",
                    f"O painel de **{categoria.name}** foi criado com sucesso em {target_channel.mention}\n"
                    f"**Link:** [Clique aqui]({message.jump_url})"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                embed=self.embed_builder.create_error_embed(
                    "Erro ao Criar Painel",
                    f"Ocorreu um erro: {str(e)}"
                ),
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Registra views persistentes quando o bot inicia"""
        # Registra view de botão simples
        self.bot.add_view(PanelButtonView(self.bot))
        
        # Registra view de categorias
        self.bot.add_view(CategorySelectView(self.bot))


async def setup(bot):
    await bot.add_cog(PainelCog(bot))
