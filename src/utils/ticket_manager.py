import discord
from datetime import datetime
from typing import Optional
import io

class TicketManager:
    """Gerenciador de operações de tickets"""
    
    def __init__(self, bot, db, embed_builder, permission_manager):
        self.bot = bot
        self.db = db
        self.embed_builder = embed_builder
        self.permission_manager = permission_manager
    
    async def create_ticket_channel(self, guild: discord.Guild, user: discord.User, 
                                   category_name: str, reason: str, description: str, 
                                   urgency: str) -> Optional[discord.TextChannel]:
        """Cria um canal de ticket"""
        
        # Obtém configurações do servidor
        config = await self.db.get_guild_config(guild.id)
        staff_role = await self.permission_manager.get_staff_role(guild)
        
        # Define a categoria onde o ticket será criado
        category = None
        if config and config.get("open_category_id"):
            category = guild.get_channel(config["open_category_id"])
        
        # Cria as permissões do canal
        overwrites = self.permission_manager.create_ticket_overwrites(guild, user, staff_role)
        
        # Gera nome do canal
        ticket_number = await self._get_next_ticket_number(guild.id)
        channel_name = f"ticket-{ticket_number:04d}"
        
        # Cria o canal
        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket de {user.name} | Categoria: {category_name}"
            )
            
            # Registra no banco de dados
            ticket_id = await self.db.create_ticket(
                guild_id=guild.id,
                channel_id=channel.id,
                user_id=user.id,
                category=category_name,
                reason=reason,
                description=description,
                urgency=urgency
            )
            
            # Adiciona log de criação
            await self.db.add_log(
                ticket_id=ticket_id,
                user_id=user.id,
                action="created",
                details=f"Categoria: {category_name}, Urgência: {urgency}"
            )
            
            return channel
            
        except Exception as e:
            print(f"Erro ao criar canal de ticket: {e}")
            return None
    
    async def _get_next_ticket_number(self, guild_id: int) -> int:
        """Obtém o próximo número de ticket disponível"""
        # Implementação simples - pode ser melhorada
        import random
        return random.randint(1, 9999)
    
    async def send_ticket_message(self, channel: discord.TextChannel, user: discord.User,
                                 category: str, reason: str, description: str, urgency: str):
        """Envia a mensagem inicial do ticket com botões"""
        
        # Cria o embed
        embed = self.embed_builder.create_ticket_embed(
            user=user,
            category=category,
            reason=reason,
            description=description,
            urgency=urgency
        )
        
        # Cria os botões
        view = TicketControlView(self.bot, self.db, self.embed_builder, self.permission_manager)
        
        # Envia mensagem de boas-vindas
        welcome_msg = (
            f"👋 Olá {user.mention}!\n\n"
            f"Seu ticket foi criado com sucesso. Nossa equipe será notificada e "
            f"irá atendê-lo em breve.\n\n"
            f"**Aguarde o atendimento de um membro da equipe.**"
        )
        
        await channel.send(content=welcome_msg)
        await channel.send(embed=embed, view=view)
    
    async def generate_transcript(self, channel: discord.TextChannel) -> io.BytesIO:
        """Gera uma transcrição do canal em formato TXT"""
        
        transcript = f"Transcrição do Ticket: {channel.name}\n"
        transcript += f"Canal ID: {channel.id}\n"
        transcript += f"Criado em: {channel.created_at.strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
        transcript += "=" * 80 + "\n\n"
        
        # Obtém todas as mensagens do canal
        messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            messages.append(message)
        
        for msg in messages:
            timestamp = msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
            author = f"{msg.author.name}#{msg.author.discriminator}"
            
            transcript += f"[{timestamp}] {author}:\n"
            
            if msg.content:
                transcript += f"{msg.content}\n"
            
            if msg.embeds:
                transcript += "[Embed anexado]\n"
            
            if msg.attachments:
                for attachment in msg.attachments:
                    transcript += f"[Anexo: {attachment.filename}]\n"
            
            transcript += "\n"
        
        transcript += "=" * 80 + "\n"
        transcript += f"Fim da transcrição - {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
        
        # Converte para BytesIO
        transcript_file = io.BytesIO(transcript.encode('utf-8'))
        transcript_file.seek(0)
        
        return transcript_file
    
    async def close_ticket(self, channel: discord.TextChannel, closer: discord.Member, 
                          reason: Optional[str] = None):
        """Fecha um ticket"""
        
        # Obtém dados do ticket
        ticket_data = await self.db.get_ticket_by_channel(channel.id)
        if not ticket_data:
            return False
        
        # Atualiza no banco de dados
        await self.db.close_ticket(channel.id, reason)
        
        # Adiciona log
        await self.db.add_log(
            ticket_id=ticket_data['ticket_id'],
            user_id=closer.id,
            action="closed",
            details=reason
        )
        
        # Move para categoria de fechados (se configurado)
        config = await self.db.get_guild_config(channel.guild.id)
        if config and config.get("closed_category_id"):
            closed_category = channel.guild.get_channel(config["closed_category_id"])
            if closed_category:
                await channel.edit(category=closed_category)
        
        # Atualiza permissões (remove acesso do usuário)
        user = channel.guild.get_member(ticket_data['user_id'])
        if user:
            await channel.set_permissions(user, view_channel=False)
        
        # Envia mensagem de fechamento
        embed = self.embed_builder.create_info_embed(
            title="Ticket Fechado",
            description=(
                f"Este ticket foi fechado por {closer.mention}.\n"
                f"**Motivo:** {reason if reason else 'Não especificado'}\n\n"
                f"O canal será deletado em breve."
            )
        )
        
        await channel.send(embed=embed)
        
        return True
    
    async def delete_ticket(self, channel: discord.TextChannel, deleter: discord.Member):
        """Deleta um ticket e envia transcrição para logs"""
        
        # Obtém dados do ticket
        ticket_data = await self.db.get_ticket_by_channel(channel.id)
        if not ticket_data:
            return False
        
        # Gera transcrição
        transcript = await self.generate_transcript(channel)
        
        # Envia para canal de logs
        config = await self.db.get_guild_config(channel.guild.id)
        if config and config.get("log_channel_id"):
            log_channel = channel.guild.get_channel(config["log_channel_id"])
            if log_channel:
                user = channel.guild.get_member(ticket_data['user_id'])
                
                embed = self.embed_builder.create_log_embed(
                    action="deleted",
                    ticket_data=ticket_data,
                    user=user or deleter,
                    reason=ticket_data.get('close_reason')
                )
                
                file = discord.File(
                    transcript,
                    filename=f"transcript-{channel.name}.txt"
                )
                
                await log_channel.send(embed=embed, file=file)
        
        # Adiciona log
        await self.db.add_log(
            ticket_id=ticket_data['ticket_id'],
            user_id=deleter.id,
            action="deleted",
            details="Canal deletado"
        )
        
        # Deleta o canal
        await channel.delete(reason=f"Ticket deletado por {deleter.name}")
        
        return True


class TicketControlView(discord.ui.View):
    """View com botões de controle do ticket"""
    
    def __init__(self, bot, db, embed_builder, permission_manager):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.embed_builder = embed_builder
        self.permission_manager = permission_manager
    
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="✋", custom_id="ticket_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para staff assumir o ticket"""
        
        # Verifica se é staff
        if not await self.permission_manager.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas membros da equipe podem assumir tickets."
                ),
                ephemeral=True
            )
            return
        
        # Obtém dados do ticket
        ticket_data = await self.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket_data:
            await interaction.response.send_message("Erro: Ticket não encontrado.", ephemeral=True)
            return
        
        # Verifica se já está claimed
        if ticket_data['claimed_by']:
            claimer = interaction.guild.get_member(ticket_data['claimed_by'])
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Ticket já Assumido",
                    f"Este ticket já está sendo atendido por {claimer.mention if claimer else 'outro staff'}."
                ),
                ephemeral=True
            )
            return
        
        # Marca como claimed
        await self.db.claim_ticket(interaction.channel.id, interaction.user.id)
        
        # Adiciona log
        await self.db.add_log(
            ticket_id=ticket_data['ticket_id'],
            user_id=interaction.user.id,
            action="claimed",
            details=f"Assumido por {interaction.user.name}"
        )
        
        # Atualiza o embed
        user = interaction.guild.get_member(ticket_data['user_id'])
        embed = self.embed_builder.create_ticket_embed(
            user=user,
            category=ticket_data['category'],
            reason=ticket_data['reason'],
            description=ticket_data['description'],
            urgency=ticket_data['urgency'],
            claimed_by=interaction.user
        )
        
        # Remove botão de claim
        new_view = TicketControlView(self.bot, self.db, self.embed_builder, self.permission_manager)
        new_view.claim_button.disabled = True
        new_view.disclaim_button.disabled = False
        
        await interaction.message.edit(embed=embed, view=new_view)
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_success_embed(
                "Ticket Assumido",
                f"{interaction.user.mention} agora é responsável por este ticket."
            )
        )
    
    @discord.ui.button(label="Disclaim", style=discord.ButtonStyle.secondary, emoji="↩️", 
                      custom_id="ticket_disclaim", disabled=True)
    async def disclaim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para staff liberar o ticket"""
        
        # Verifica se é staff
        if not await self.permission_manager.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas membros da equipe podem liberar tickets."
                ),
                ephemeral=True
            )
            return
        
        # Obtém dados do ticket
        ticket_data = await self.db.get_ticket_by_channel(interaction.channel.id)
        if not ticket_data:
            await interaction.response.send_message("Erro: Ticket não encontrado.", ephemeral=True)
            return
        
        # Verifica se o ticket está claimed
        if not ticket_data['claimed_by']:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Ticket Não Assumido",
                    "Este ticket não foi assumido por ninguém."
                ),
                ephemeral=True
            )
            return
        
        # **VERIFICAÇÃO DE AUTORIZAÇÃO DE DESCLAIM**
        if ticket_data['claimed_by'] != interaction.user.id:
            claimer = interaction.guild.get_member(ticket_data['claimed_by'])
            claimer_mention = claimer.mention if claimer else "Staff Desconhecido"
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Autorização",
                    f"Apenas o staff que assumiu o ticket ({claimer_mention}) pode liberá-lo."
                ),
                ephemeral=True
            )
            return
        
        # Remove claim
        await self.db.disclaim_ticket(interaction.channel.id)
        
        # Adiciona log
        await self.db.add_log(
            ticket_id=ticket_data['ticket_id'],
            user_id=interaction.user.id,
            action="disclaimed",
            details=f"Liberado por {interaction.user.name}"
        )
        
        # Atualiza o embed
        user = interaction.guild.get_member(ticket_data['user_id'])
        embed = self.embed_builder.create_ticket_embed(
            user=user,
            category=ticket_data['category'],
            reason=ticket_data['reason'],
            description=ticket_data['description'],
            urgency=ticket_data['urgency']
        )
        
        # Reativa botão de claim
        new_view = TicketControlView(self.bot, self.db, self.embed_builder, self.permission_manager)
        new_view.claim_button.disabled = False
        new_view.disclaim_button.disabled = True
        
        await interaction.message.edit(embed=embed, view=new_view)
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_info_embed(
                "Ticket Liberado",
                "O ticket foi liberado e está disponível para outro staff assumir."
            )
        )
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para fechar o ticket"""
        
        # Verifica se é staff
        if not await self.permission_manager.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas membros da equipe podem fechar tickets."
                ),
                ephemeral=True
            )
            return
        
        # Abre modal para motivo
        modal = CloseTicketModal(self.bot, self.db, self.embed_builder, self.permission_manager)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Deletar", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="ticket_delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para deletar o ticket"""
        
        # Verifica se é staff
        if not await self.permission_manager.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Sem Permissão",
                    "Apenas membros da equipe podem deletar tickets."
                ),
                ephemeral=True
            )
            return
        
        # Cria view de confirmação
        confirm_view = ConfirmDeleteView(self.bot, self.db, self.embed_builder, self.permission_manager)
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_error_embed(
                "Confirmar Deleção",
                "⚠️ **ATENÇÃO:** Esta ação é irreversível!\n\n"
                "O canal será deletado permanentemente.\n"
                "Uma transcrição será enviada para o canal de logs.\n\n"
                "Deseja continuar?"
            ),
            view=confirm_view,
            ephemeral=True
        )


class CloseTicketModal(discord.ui.Modal, title="Fechar Ticket"):
    """Modal para fechar ticket com motivo"""
    
    reason = discord.ui.TextInput(
        label="Motivo do Fechamento",
        placeholder="Digite o motivo do fechamento (opcional)",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    def __init__(self, bot, db, embed_builder, permission_manager):
        super().__init__()
        self.bot = bot
        self.db = db
        self.embed_builder = embed_builder
        self.permission_manager = permission_manager
    
    async def on_submit(self, interaction: discord.Interaction):
        from utils.ticket_manager import TicketManager
        
        ticket_manager = TicketManager(self.bot, self.db, self.embed_builder, self.permission_manager)
        
        success = await ticket_manager.close_ticket(
            interaction.channel,
            interaction.user,
            str(self.reason.value) if self.reason.value else None
        )
        
        if success:
            await interaction.response.send_message(
                embed=self.embed_builder.create_success_embed(
                    "Ticket Fechado",
                    "O ticket foi fechado com sucesso."
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=self.embed_builder.create_error_embed(
                    "Erro",
                    "Não foi possível fechar o ticket."
                ),
                ephemeral=True
            )


class ConfirmDeleteView(discord.ui.View):
    """View de confirmação para deletar ticket"""
    
    def __init__(self, bot, db, embed_builder, permission_manager):
        super().__init__(timeout=60)
        self.bot = bot
        self.db = db
        self.embed_builder = embed_builder
        self.permission_manager = permission_manager
    
    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        from utils.ticket_manager import TicketManager
        
        ticket_manager = TicketManager(self.bot, self.db, self.embed_builder, self.permission_manager)
        
        await interaction.response.send_message(
            embed=self.embed_builder.create_info_embed(
                "Deletando Ticket",
                "Gerando transcrição e deletando o canal..."
            ),
            ephemeral=True
        )
        
        await ticket_manager.delete_ticket(interaction.channel, interaction.user)
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=self.embed_builder.create_info_embed(
                "Cancelado",
                "A deleção do ticket foi cancelada."
            ),
            ephemeral=True
        )
        self.stop()
