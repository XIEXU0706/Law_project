from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import app as api_app
from app.database import engine
from app.models import Base

app = FastAPI(title="智能法律问答系统", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Base模型类的元数据创建

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 直接将 api 路由挂载
app.mount("/", api_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=9091, reload=True)