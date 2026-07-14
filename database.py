import asyncpg
from datetime import datetime
from config import DATABASE_URL

async def create_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def create_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users(
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    timezone TEXT DEFAULT 'ASIA/Almaty')
                    ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS categories(
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id),
                    name TEXT NOT NULL)
                           ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks(
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id),
                    category_id INT REFERENCES categories(id),
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline TIMESTAMP,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW())''')
        

async def add_user(pool, user_id: int, username: str):
    async with pool.acquire() as conn:
        await conn.fetchrow('''
        INSERT INTO users(id,username)
        VALUES($1, $2) 
        ON CONFLICT (id) DO UPDATE SET username = $2 
        RETURNING id''', user_id, username)

async def add_task(pool, user_id: int, title: str, description: str, category_id: int, deadline,priority: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow('''
        INSERT INTO tasks(user_id,title,description,category_id,deadline, priority)
        VALUES($1, $2, $3, $4, $5, $6)
        RETURNING id''', user_id,title,description,category_id,deadline,priority)
        return row['id']
    

async def get_user_tasks(pool, user_id):
    async with pool.acquire() as conn:
        return await conn.fetch('''
            SELECT t.title, t.description, t.deadline, t.priority, t.status, c.name AS category_name
            FROM tasks t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
        ''', user_id) 
    

async def get_user_categories(pool,user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetch('''
        SELECT id, name 
        FROM categories
        WHERE user_id = $1
        ''', user_id)

async def get_pending_tasks(pool,user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetch("""
        SELECT id, title, deadline
        FROM tasks
        WHERE user_id = $1 AND status = 'pending'""",user_id)
    

async def mark_task_done(pool, task_id: int):
    async with pool.acquire() as conn:
        await conn.execute("""
        UPDATE tasks SET status = 'completed' WHERE id = $1""", task_id)