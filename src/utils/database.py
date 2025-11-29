import aiosqlite
import json
from datetime import datetime
from typing import Optional, Dict, List

class Database:
    def __init__(self, db_path: str = "data/tickets.db"):
        self.db_path = db_path
        
    async def init_db(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tabela de configurações do servidor
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id INTEGER PRIMARY KEY,
                    staff_role_id INTEGER,
                    log_channel_id INTEGER,
                    open_category_id INTEGER,
                    closed_category_id INTEGER,
                    config_data TEXT
                )
            """)
            
            # Tabela de tickets
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER UNIQUE,
                    user_id INTEGER,
                    category TEXT,
                    reason TEXT,
                    description TEXT,
                    urgency TEXT,
                    claimed_by INTEGER,
                    status TEXT DEFAULT 'open',
                    created_at TEXT,
                    closed_at TEXT,
                    close_reason TEXT
                )
            """)
            
            # Tabela de painéis fixos
            await db.execute("""
                CREATE TABLE IF NOT EXISTS panels (
                    panel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_id INTEGER UNIQUE,
                    panel_type TEXT,
                    created_at TEXT
                )
            """)
            
            # Tabela de logs de ações
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            """)
            
            await db.commit()
    
    # ===== CONFIGURAÇÕES DO SERVIDOR =====
    async def get_guild_config(self, guild_id: int) -> Optional[Dict]:
        """Obtém a configuração de um servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM guild_config WHERE guild_id = ?", 
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "guild_id": row[0],
                        "staff_role_id": row[1],
                        "log_channel_id": row[2],
                        "open_category_id": row[3],
                        "closed_category_id": row[4],
                        "config_data": json.loads(row[5]) if row[5] else {}
                    }
                return None
    
    async def set_guild_config(self, guild_id: int, **kwargs):
        """Define ou atualiza configurações do servidor"""
        async with aiosqlite.connect(self.db_path) as db:
            config = await self.get_guild_config(guild_id)
            
            if config:
                # Atualizar configuração existente
                updates = []
                values = []
                for key, value in kwargs.items():
                    if key == "config_data":
                        value = json.dumps(value)
                    updates.append(f"{key} = ?")
                    values.append(value)
                
                values.append(guild_id)
                query = f"UPDATE guild_config SET {', '.join(updates)} WHERE guild_id = ?"
                await db.execute(query, values)
            else:
                # Criar nova configuração
                await db.execute(
                    """INSERT INTO guild_config 
                       (guild_id, staff_role_id, log_channel_id, open_category_id, closed_category_id, config_data)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        guild_id,
                        kwargs.get("staff_role_id"),
                        kwargs.get("log_channel_id"),
                        kwargs.get("open_category_id"),
                        kwargs.get("closed_category_id"),
                        json.dumps(kwargs.get("config_data", {}))
                    )
                )
            
            await db.commit()
    
    # ===== TICKETS =====
    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int, 
                           category: str, reason: str, description: str, urgency: str) -> int:
        """Cria um novo ticket e retorna o ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO tickets 
                   (guild_id, channel_id, user_id, category, reason, description, urgency, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (guild_id, channel_id, user_id, category, reason, description, urgency, 
                 datetime.utcnow().isoformat())
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict]:
        """Obtém informações de um ticket pelo ID do canal"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM tickets WHERE channel_id = ?", 
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "ticket_id": row[0],
                        "guild_id": row[1],
                        "channel_id": row[2],
                        "user_id": row[3],
                        "category": row[4],
                        "reason": row[5],
                        "description": row[6],
                        "urgency": row[7],
                        "claimed_by": row[8],
                        "status": row[9],
                        "created_at": row[10],
                        "closed_at": row[11],
                        "close_reason": row[12]
                    }
                return None
    
    async def get_user_open_tickets(self, guild_id: int, user_id: int) -> List[Dict]:
        """Obtém todos os tickets abertos de um usuário"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'open'",
                (guild_id, user_id)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "ticket_id": row[0],
                        "channel_id": row[2],
                        "category": row[4]
                    }
                    for row in rows
                ]
    
    async def claim_ticket(self, channel_id: int, staff_id: int):
        """Marca um ticket como claimed por um staff"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tickets SET claimed_by = ? WHERE channel_id = ?",
                (staff_id, channel_id)
            )
            await db.commit()
    
    async def disclaim_ticket(self, channel_id: int):
        """Remove o claim de um ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tickets SET claimed_by = NULL WHERE channel_id = ?",
                (channel_id,)
            )
            await db.commit()
    
    async def close_ticket(self, channel_id: int, close_reason: str = None):
        """Fecha um ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tickets SET status = 'closed', closed_at = ?, close_reason = ? WHERE channel_id = ?",
                (datetime.utcnow().isoformat(), close_reason, channel_id)
            )
            await db.commit()
    
    # ===== PAINÉIS =====
    async def create_panel(self, guild_id: int, channel_id: int, message_id: int, panel_type: str):
        """Registra um painel fixo"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO panels (guild_id, channel_id, message_id, panel_type, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (guild_id, channel_id, message_id, panel_type, datetime.utcnow().isoformat())
            )
            await db.commit()
    
    async def get_panel(self, message_id: int) -> Optional[Dict]:
        """Obtém informações de um painel"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM panels WHERE message_id = ?",
                (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "panel_id": row[0],
                        "guild_id": row[1],
                        "channel_id": row[2],
                        "message_id": row[3],
                        "panel_type": row[4],
                        "created_at": row[5]
                    }
                return None
    
    # ===== LOGS =====
    async def add_log(self, ticket_id: int, user_id: int, action: str, details: str = None):
        """Adiciona um log de ação em um ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO ticket_logs (ticket_id, user_id, action, details, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (ticket_id, user_id, action, details, datetime.utcnow().isoformat())
            )
            await db.commit()
    
    async def get_ticket_logs(self, ticket_id: int) -> List[Dict]:
        """Obtém todos os logs de um ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM ticket_logs WHERE ticket_id = ? ORDER BY timestamp ASC",
                (ticket_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "log_id": row[0],
                        "ticket_id": row[1],
                        "user_id": row[2],
                        "action": row[3],
                        "details": row[4],
                        "timestamp": row[5]
                    }
                    for row in rows
                ]
