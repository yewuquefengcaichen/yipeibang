"""
数据库初始化和操作工具
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent.parent / "data" / "yipeibang.db"


def init_database():
    """初始化数据库，创建所有表"""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 对话会话表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL DEFAULT 'default_user',
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        message_count INTEGER DEFAULT 0
    )
    """)

    # 消息表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
        content TEXT NOT NULL,
        intent_data TEXT,
        tokens INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)

    # 记忆表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        source TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 0,
        last_accessed TIMESTAMP
    )
    """)

    # 提醒表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        trigger_time TIMESTAMP NOT NULL,
        trigger_type TEXT NOT NULL CHECK(trigger_type IN ('once', 'daily', 'weekly')),
        priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'triggered', 'read', 'dismissed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        triggered_at TIMESTAMP,
        read_at TIMESTAMP
    )
    """)

    # 知识库元数据表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_items (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        category TEXT NOT NULL,
        tags TEXT,
        source TEXT,
        vector_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 0
    )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_trigger ON reminders(trigger_time, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_items(category)")

    conn.commit()
    conn.close()

    print(f"Database initialized: {DB_PATH}")


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 返回字典格式
    return conn


def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """将Row对象转换为字典"""
    return {key: row[key] for key in row.keys()}


# ========== 对话相关 ==========

def save_message(conversation_id: str, role: str, content: str, intent_data: Optional[Dict] = None) -> str:
    """保存消息"""
    import uuid
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, intent_data)
        VALUES (?, ?, ?, ?, ?)
    """, (message_id, conversation_id, role, content, json.dumps(intent_data) if intent_data else None))

    # 更新会话的消息计数
    cursor.execute("""
        UPDATE conversations
        SET message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (conversation_id,))

    conn.commit()
    conn.close()

    return message_id


def get_conversation_history(conversation_id: str, limit: int = 50) -> List[Dict]:
    """获取对话历史"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (conversation_id, limit))

    messages = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    # 解析intent_data
    for msg in messages:
        if msg['intent_data']:
            msg['intent_data'] = json.loads(msg['intent_data'])

    return list(reversed(messages))


def create_conversation(title: Optional[str] = None) -> str:
    """创建新对话"""
    import uuid
    conversation_id = f"conv_{uuid.uuid4().hex[:12]}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversations (id, title)
        VALUES (?, ?)
    """, (conversation_id, title or "新对话"))

    conn.commit()
    conn.close()

    return conversation_id


# ========== 记忆相关 ==========

def save_memory(user_id: str = "default_user", category: str = "其他", content: str = "",
                key: str = None, value: str = None, source: str = "用户输入",
                conversation_id: str = None) -> str:
    """保存记忆（兼容旧版和新版接口）"""
    import uuid
    memory_id = f"mem_{uuid.uuid4().hex[:12]}"

    conn = get_connection()
    cursor = conn.cursor()

    # 兼容旧版接口
    if key and value and not content:
        content = f"{key}: {value}"

    cursor.execute("""
        INSERT INTO memories (id, category, key, value, source)
        VALUES (?, ?, ?, ?, ?)
    """, (memory_id, category, user_id or "default_user", content, source))

    conn.commit()
    conn.close()

    return memory_id


def get_memories(user_id: str = "default_user", category: Optional[str] = None) -> List[Dict]:
    """获取记忆列表（新版接口）"""
    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT id, category, value as content, source, created_at
            FROM memories
            WHERE key = ? AND category = ?
            ORDER BY created_at DESC
        """, (user_id, category))
    else:
        cursor.execute("""
            SELECT id, category, value as content, source, created_at
            FROM memories
            WHERE key = ?
            ORDER BY created_at DESC
        """, (user_id,))

    memories = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    return memories


def delete_memory(memory_id: str) -> bool:
    """删除记忆"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Delete memory error: {e}")
        return False
    finally:
        conn.close()


def get_all_memories(category: Optional[str] = None) -> List[Dict]:
    """获取所有记忆"""
    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC", (category,))
    else:
        cursor.execute("SELECT * FROM memories ORDER BY updated_at DESC")

    memories = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    return memories


def update_memory(memory_id: str, value: str):
    """更新记忆"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE memories
        SET value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (value, memory_id))

    conn.commit()
    conn.close()


def delete_memory(memory_id: str):
    """删除记忆"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    conn.commit()
    conn.close()


# ========== 提醒相关 ==========

def create_reminder(reminder_data: Dict) -> str:
    """创建提醒"""
    import uuid
    reminder_id = f"rem_{uuid.uuid4().hex[:12]}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reminders (id, type, title, content, trigger_time, trigger_type, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        reminder_id,
        reminder_data['type'],
        reminder_data['title'],
        reminder_data['content'],
        reminder_data['trigger_time'],
        reminder_data.get('trigger_type', 'once'),
        reminder_data.get('priority', 'medium')
    ))

    conn.commit()
    conn.close()

    return reminder_id


def get_active_reminders() -> List[Dict]:
    """获取所有未完成的提醒"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM reminders
        WHERE status = 'pending'
        ORDER BY trigger_time ASC
    """)

    reminders = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    return reminders


def update_reminder_status(reminder_id: str, status: str):
    """更新提醒状态"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reminders
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, reminder_id))

    conn.commit()
    conn.close()


def get_pending_reminders() -> List[Dict]:
    """获取待触发的提醒"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM reminders
        WHERE status = 'pending' AND trigger_time <= CURRENT_TIMESTAMP
        ORDER BY trigger_time
    """)

    reminders = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()

    return reminders


def mark_reminder_read(reminder_id: str):
    """标记提醒为已读"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reminders
        SET status = 'read', read_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (reminder_id,))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # 初始化数据库
    init_database()
