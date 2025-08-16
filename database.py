
import aiosqlite
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_points.db"):
        self.db_path = db_path
    
    async def init_database(self):
        """Initialize the database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    total_points INTEGER DEFAULT 0,
                    msg_count INTEGER DEFAULT 0,
                    reactions_given INTEGER DEFAULT 0,
                    reactions_received INTEGER DEFAULT 0,
                    voice_minutes INTEGER DEFAULT 0,
                    last_message_time INTEGER DEFAULT 0
                )
            """)
            
            # Point history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS point_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    points INTEGER,
                    reason TEXT,
                    timestamp INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def get_user_points(self, user_id: int) -> Optional[Tuple]:
        """Get user points and stats"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT username, total_points, msg_count, reactions_given, reactions_received, voice_minutes
                FROM users WHERE user_id = ?
            """, (user_id,))
            return await cursor.fetchone()
    
    async def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get user's rank position"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) + 1 FROM users 
                WHERE total_points > (SELECT total_points FROM users WHERE user_id = ?)
            """, (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple]:
        """Get top users leaderboard"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT username, total_points, user_id FROM users 
                ORDER BY total_points DESC LIMIT ?
            """, (limit,))
            return await cursor.fetchall()
    
    async def update_user_points(self, user_id: int, username: str, points: int, reason: str = "message"):
        """Update user points and stats"""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert or update user
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, total_points, msg_count)
                VALUES (?, ?, COALESCE((SELECT total_points FROM users WHERE user_id = ?), 0) + ?, 
                        COALESCE((SELECT msg_count FROM users WHERE user_id = ?), 0) + 1)
            """, (user_id, username, user_id, points, user_id))
            
            # Add to history
            await db.execute("""
                INSERT INTO point_history (user_id, points, reason, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, points, reason, int(__import__('time').time())))
            
            await db.commit()
