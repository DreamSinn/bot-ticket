import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class AdminCog(commands.Cog):
    """Cog para comandos administrativos e configuração"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.embed_builder = bot.embed_builder
        self.permission_manager = bot.permission_manager
    
    config_group = app_commands.Group(
        name="config",
        description="Comandos de configuração do sistema de tickets"
    )
    
    @config_group.command(name="staff", description="Define o cargo de staff")
    @app_commands.describe(cargo="Cargo que terá permissões de staff")
    async def config_staff(self, interaction: discord.Interaction, cargo: discord.Role):
        """Define o cargo de staff"""
        
        # Verifica se é administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas administradores podem configurar o bot."
                ),
                ephemeral=True
            )
            return
        
        await self.db.set_guild_config(
            guild_id=interaction.guild.id,
            staff_role_id=cargo.id
        )
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_success_embed(
                "Cargo de Staff Configurado",
                f"O cargo {cargo.mention} agora tem permissões de staff.\n\n"
                f"Membros com este cargo poderão:\n"
                f"• Assumir tickets (claim)\n"
                f"• Fechar tickets\n"
                f"• Deletar tickets\n"
                f"• Criar painéis"
            ),
            ephemeral=True
        )
    
    @config_group.command(name="logs", description="Define o canal de logs")
    @app_commands.describe(canal="Canal onde os logs serão enviados")
    async def config_logs(self, interaction: discord.Interaction, canal: discord.TextChannel):
        """Define o canal de logs"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas administradores podem configurar o bot."
                ),
                ephemeral=True
            )
            return
        
        # Verifica se o bot pode enviar mensagens no canal
        if not canal.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    f"Não tenho permissão para enviar mensagens em {canal.mention}"
                ),
                ephemeral=True
            )
            return
        
        await self.db.set_guild_config(
            guild_id=interaction.guild.id,
            log_channel_id=canal.id
        )
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_success_embed(
                "Canal de Logs Configurado",
                f"Os logs do sistema de tickets serão enviados em {canal.mention}\n\n"
                f"**Logs incluem:**\n"
                f"• Criação de tickets\n"
                f"• Claims e disclaims\n"
                f"• Fechamentos\n"
                f"• Deleções com transcrições"
            ),
            ephemeral=True
        )
        
        # Envia mensagem de teste no canal de logs
        test_embed = discord.Embed(
            title="✅ Sistema de Logs Ativado",
            description="Este canal foi configurado para receber logs do sistema de tickets.",
            color=0x00FF00,
            timestamp=discord.utils.utcnow()
        )
        test_embed.set_footer(text=f"{self.embed_builder.bot_name} • Log System")
        
        await canal.send(embed=test_embed)
    
    @config_group.command(name="categoria-abertos", description="Define a categoria para tickets abertos")
    @app_commands.describe(categoria="Categoria onde os tickets abertos serão criados")
    async def config_open_category(self, interaction: discord.Interaction, categoria: discord.CategoryChannel):
        """Define a categoria para tickets abertos"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas administradores podem configurar o bot."
                ),
                ephemeral=True
            )
            return
        
        await self.db.set_guild_config(
            guild_id=interaction.guild.id,
            open_category_id=categoria.id
        )
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_success_embed(
                "Categoria de Tickets Abertos Configurada",
                f"Novos tickets serão criados na categoria **{categoria.name}**"
            ),
            ephemeral=True
        )
    
    @config_group.command(name="categoria-fechados", description="Define a categoria para tickets fechados")
    @app_commands.describe(categoria="Categoria onde os tickets fechados serão movidos")
    async def config_closed_category(self, interaction: discord.Interaction, categoria: discord.CategoryChannel):
        """Define a categoria para tickets fechados"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas administradores podem configurar o bot."
                ),
                ephemeral=True
            )
            return
        
        await self.db.set_guild_config(
            guild_id=interaction.guild.id,
            closed_category_id=categoria.id
        )
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_success_embed(
                "Categoria de Tickets Fechados Configurada",
                f"Tickets fechados serão movidos para a categoria **{categoria.name}**"
            ),
            ephemeral=True
        )
    
    @config_group.command(name="ver", description="Visualiza as configurações atuais")
    async def config_view(self, interaction: discord.Interaction):
        """Visualiza as configurações do servidor"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas administradores podem ver as configurações."
                ),
                ephemeral=True
            )
            return
        
        config = await self.db.get_guild_config(interaction.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Configurações do Sistema de Tickets",
            description="Configurações atuais do servidor",
            color=self.embed_builder.color,
            timestamp=discord.utils.utcnow()
        )
        
        if config:
            # Cargo de staff
            staff_role = interaction.guild.get_role(config.get("staff_role_id")) if config.get("staff_role_id") else None
            embed.add_field(
                name="👥 Cargo de Staff",
                value=staff_role.mention if staff_role else "❌ Não configurado",
                inline=False
            )
            
            # Canal de logs
            log_channel = interaction.guild.get_channel(config.get("log_channel_id")) if config.get("log_channel_id") else None
            embed.add_field(
                name="📋 Canal de Logs",
                value=log_channel.mention if log_channel else "❌ Não configurado",
                inline=False
            )
            
            # Categoria de tickets abertos
            open_category = interaction.guild.get_channel(config.get("open_category_id")) if config.get("open_category_id") else None
            embed.add_field(
                name="📂 Categoria - Tickets Abertos",
                value=f"**{open_category.name}**" if open_category else "❌ Não configurado",
                inline=True
            )
            
            # Categoria de tickets fechados
            closed_category = interaction.guild.get_channel(config.get("closed_category_id")) if config.get("closed_category_id") else None
            embed.add_field(
                name="🔒 Categoria - Tickets Fechados",
                value=f"**{closed_category.name}**" if closed_category else "❌ Não configurado",
                inline=True
            )
        else:
            embed.description = "⚠️ Nenhuma configuração encontrada. Use os comandos `/config` para configurar o bot."
        
        embed.set_footer(text=f"{self.embed_builder.bot_name} • Configuration")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="setup", description="Configuração rápida inicial do bot")
    async def setup_wizard(self, interaction: discord.Interaction):
        """Wizard de configuração inicial"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas administradores podem executar o setup."
                ),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🚀 Setup Inicial do Sistema de Tickets",
            description=(
                "Bem-vindo ao assistente de configuração!\n\n"
                "**Para configurar o bot, use os seguintes comandos:**\n\n"
                "**1️⃣ Configurar cargo de staff:**\n"
                "`/config staff cargo:@Staff`\n\n"
                "**2️⃣ Configurar canal de logs:**\n"
                "`/config logs canal:#logs-tickets`\n\n"
                "**3️⃣ Configurar categoria para tickets abertos:**\n"
                "`/config categoria-abertos categoria:Tickets`\n\n"
                "**4️⃣ Configurar categoria para tickets fechados (opcional):**\n"
                "`/config categoria-fechados categoria:Tickets Fechados`\n\n"
                "**5️⃣ Criar um painel de tickets:**\n"
                "`/painel criar tipo:Simples`\n"
                "ou\n"
                "`/painel criar tipo:Com Categorias`\n\n"
                "**📝 Comandos disponíveis:**\n"
                "• `/ticket` - Usuários podem criar tickets\n"
                "• `/painel criar` - Staff pode criar painéis fixos\n"
                "• `/painel categoria` - Criar painel de categoria específica\n"
                "• `/config ver` - Ver configurações atuais"
            ),
            color=self.embed_builder.color,
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{self.embed_builder.bot_name} • Setup Wizard")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
