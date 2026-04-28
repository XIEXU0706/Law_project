import asyncio
from app.database import engine
from app.models import Base, ChatSession, Message

async def init():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print('Tables created successfully!')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(init())
