import discord
from discord.ext import commands
from typing import Optional

class PermissionManager:
    """Gerenciador de permissões do bot"""
    
    def __init__(self, db):
        self.db = db
    
    async def is_staff(self, member: discord.Member) -> bool:
        """Verifica se um membro é staff"""
        # Verifica se tem permissão de administrador
        if member.guild_permissions.administrator:
            return True
        
        # Verifica se tem o cargo de staff configurado
        config = await self.db.get_guild_config(member.guild.id)
        if config and config.get("staff_role_id"):
            staff_role = member.guild.get_role(config["staff_role_id"])
            if staff_role and staff_role in member.roles:
                return True
        
        return False
    
    async def get_staff_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        """Obtém o cargo de staff configurado"""
        config = await self.db.get_guild_config(guild.id)
        if config and config.get("staff_role_id"):
            return guild.get_role(config["staff_role_id"])
        return None
    
    def create_ticket_overwrites(self, guild: discord.Guild, user: discord.User, 
                                 staff_role: Optional[discord.Role] = None) -> dict:
        """Cria as permissões para o canal de ticket"""
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
        }
        
        # Adiciona permissões para staff se configurado
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                manage_messages=True
            )
        
        return overwrites

def staff_only():
    """Decorator para comandos apenas para staff"""
    async def predicate(ctx):
        if isinstance(ctx, discord.Interaction):
            member = ctx.user
            guild = ctx.guild
        else:
            member = ctx.author
            guild = ctx.guild
        
        if not guild:
            return False
        
        # Administradores sempre têm acesso
        if member.guild_permissions.administrator:
            return True
        
        # Verifica cargo de staff no banco de dados
        from utils.database import Database
        db = Database()
        config = await db.get_guild_config(guild.id)
        
        if config and config.get("staff_role_id"):
            staff_role = guild.get_role(config["staff_role_id"])
            if staff_role and staff_role in member.roles:
                return True
        
        return False
    
    return commands.check(predicate)
