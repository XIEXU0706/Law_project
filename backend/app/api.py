import json
import pdfplumber
import docx
import io
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from typing import List

from app.database import get_db
from app.models import ChatSession, Message
from app.agent import agent

app = FastAPI()

class QuestionRequest(BaseModel):
    query: str
    session_id: str
    file_name: Optional[str] = None
    file_content: Optional[str] = None
    deep_think: Optional[bool] = False

class SessionUpdate(BaseModel):
    title: str

@app.put("/sessions/{session_id}")
async def update_session(session_id: str, request: SessionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.title = request.title
        await db.commit()
        return {"status": "success", "title": session.title}
    return {"status": "error", "msg": "not found"}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
        return {"status": "success"}
    return {"status": "error", "msg": "not found"}

@app.get("/sessions")
async def get_all_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).order_by(ChatSession.create_time.desc()))
    return result.scalars().all()

@app.post("/sessions")
async def create_new_session(db: AsyncSession = Depends(get_db)):
    new_session = ChatSession(title="新会话")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.create_time))
    return result.scalars().all()

@app.post("/law_agent/ask")
async def ask_question(request: QuestionRequest, db: AsyncSession = Depends(get_db)):
    # 保存用户发来的问题
    user_msg = Message(session_id=request.session_id, role="user", content=request.query)
    db.add(user_msg)
    await db.commit()

    # 获取当前会话信息（如果标题是新会话，则用第一句话更新它）
    session_result = await db.execute(select(ChatSession).where(ChatSession.id == request.session_id))
    current_session = session_result.scalar_one_or_none()
    if current_session and current_session.title == "新会话":
        current_session.title = request.query[:15] + "..." if len(request.query) > 15 else request.query
        await db.commit()

    async def generate():
        user_input = request.query
        if request.file_content:
            user_input = f"用户上传了文件《{request.file_name}》，内容如下：\n{request.file_content}\n\n用户问题：{request.query}"

        from app.agent import get_agent
        current_agent = get_agent(request.deep_think)

        response_stream = current_agent.stream({
            "messages": [
                {"role": "user", "content": user_input}
            ]
        }, stream_mode="messages")
        
        full_ai_content = ""
        reasoning_started = False
        content_started = False

        for chunk, metadata in response_stream:
            if metadata.get("langgraph_node") == "agent":
                # Langchain 的 BaseMessage chunk 里可能有多种携带推理信息的方式
                reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                
                # 有些 OpenAI 格式可能会放在 message.content 列表的特定块中或用其他的 dict 存放
                # 注意处理：
                content = chunk.content

                if reasoning:
                    if not reasoning_started:
                        reasoning_started = True
                        prefix = "```text\n[深度思考过程]\n"
                        full_ai_content += prefix
                        yield f"data: {json.dumps({'content': prefix}, ensure_ascii=False)}\n\n"
                    
                    full_ai_content += reasoning
                    yield f"data: {json.dumps({'content': reasoning}, ensure_ascii=False)}\n\n"
                
                elif content:
                    # 如果是从推理切换到正文，或者根本没有推理，直接到正文
                    # 遇到正文后，如果之前有推理并还没闭合代码块，赶紧闭合
                    if reasoning_started and not content_started:
                        content_started = True
                        suffix = "\n```\n\n"
                        full_ai_content += suffix
                        yield f"data: {json.dumps({'content': suffix}, ensure_ascii=False)}\n\n"
                        
                    full_ai_content += content
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

        # 如果一直在 reasoning (虽然很罕见)，确保代码块闭合
        if reasoning_started and not content_started:
            suffix = "\n```\n\n"
            full_ai_content += suffix
            yield f"data: {json.dumps({'content': suffix}, ensure_ascii=False)}\n\n"

        # 思考和文本生成结束后，在同一个数据库中异步存放 ai 回答
        async for session in get_db():
            ai_msg = Message(session_id=request.session_id, role="ai", content=full_ai_content)
            session.add(ai_msg)
            await session.commit()
            break

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = ""
    try:
        if file.filename.endswith(".pdf"):
            file_bytes = await file.read()
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif file.filename.endswith(".docx"):
            file_bytes = await file.read()
            doc = docx.Document(io.BytesIO(file_bytes))
            content = "\n".join([para.text for para in doc.paragraphs])
        elif file.filename.endswith(".txt"):
            file_bytes = await file.read()
            content = file_bytes.decode('utf-8')
        else:
            return {"error": "Unsupported file format. Please upload PDF, DOCX, or TXT."}
            
        return {"filename": file.filename, "content": content}
    except Exception as e:
        return {"error": str(e)}