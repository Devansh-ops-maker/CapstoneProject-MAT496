import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
from config import config

class MemoryManager:
    def __init__(self):
        self.db_path = config.database_path
        self.setup_database()
        
    def setup_database(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, memory_key)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_session ON conversations (user_id, session_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_memories ON user_memories (user_id)
        ''')
        
        self.conn.commit()
    
    def store_conversation(self, user_id: str, session_id: str, message: str, response: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (user_id, session_id, message, response)
            VALUES (?, ?, ?, ?)
        ''', (user_id, session_id, message, response))
        self.conn.commit()
    
    def store_memory(self, user_id: str, memory_key: str, memory_value: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_memories (user_id, memory_key, memory_value)
            VALUES (?, ?, ?)
        ''', (user_id, memory_key, memory_value))
        self.conn.commit()
    
    def get_user_memories(self, user_id: str) -> Dict[str, str]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT memory_key, memory_value
            FROM user_memories 
            WHERE user_id = ?
        ''', (user_id,))
        
        memories = {}
        for key, value in cursor.fetchall():
            memories[key] = value
        return memories
    
    def get_recent_conversations(self, user_id: str, session_id: str, limit: int = None) -> List[Dict]:
        if limit is None:
            limit = config.max_conversation_history
            
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT message, response
            FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, session_id, limit))
        
        results = cursor.fetchall()
        conversations = []
        for message, response in results:
            conversations.append({
                'message': message,
                'response': response
            })
        
        return conversations[::-1]
    
    def close(self):
        if self.conn:
            self.conn.close()
