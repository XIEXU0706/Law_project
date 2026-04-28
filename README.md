# ⚖️ KNOW-LAW 智能法律助手

本项目是一个垂直领域的**智能法律问答系统**，旨在通过本地知识库结合大语言模型，为用户提供精准的法律咨询服务。项目在前端采用极简高交互UI设计，并在后端首批接入并适配了推理型大模型（如DeepSeek-chat、 DeepSeek-Reasoner），支持流式展现 AI 的**“深度思考”**全过程。

## ✨ 核心特性 

- **🧠 深度思考（Reasoning Streaming）**：独家适配推理型大模型的 SSE 流式输出格式。前端支持实时分离、打字机式渲染大模型的“内在推理过程”（Thought Process）与最终回答。
- **📚 检索增强生成 (RAG)**：通过集成本地法律文档文件，使用 `ChromaDB` 构建本地向量知识库，结合 `LangGraph` 智能体路由，有效解决了大模型直接回答法律问题时易产生的“幻觉”。
- **⚡ 双模型动态路由**：支持“常规对话”与“深度思考”模式无缝热切，通过后端动态管理 Agent 工作流实例化。
- **🎨 纯享版深度交互 UI**：自研 Vue 前端界面，具有动态侧边栏、响应式悬浮输入框、流式长文本平滑滚动、以及完善的 Markdown / 代码块渲染。

## 🛠️ 技术栈

**后端 (Backend):**
- 框架：[FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- AI 编排 / Agent：[LangChain](https://python.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/)
- 向量引擎库：ChromaDB
- 通信机制：SSE (Server-Sent Events) 流式传输

**前端 (Frontend):**
- 框架：[Vue.js](https://vuejs.org/) + Element UI
- 布局方案：纯 CSS Flexbox 响应式架构
- 文本渲染：Markdown-it

## 🚀 快速启动

### 1. 克隆项目
```bash
git clone https://github.com/XIEXU0706/Law_project.git
cd Law_project
