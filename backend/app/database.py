
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from app.models import ChatSession, Message
from sqlalchemy import select, delete, update

ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/law_db?charset=utf8"
# 创建异步引擎
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 是否打印SQL语句
    pool_size=30,  # 设置连接池中保持的持久连接数
    max_overflow=50  # 设置连接池中允许的最大连接数
)


# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,  # 绑定数据库引擎
    class_=AsyncSession,  # 指定会话类
    expire_on_commit=False  # 设置会话在提交后是否过期
)

# 依赖项：用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 返回数据库会话，给路由处理函数
            await session.commit()  # 无异常，提交事务
        except Exception:
            await session.rollback()  # 有异常，回滚事务
            raise
        finally:
            await session.close()  # 关闭会话
