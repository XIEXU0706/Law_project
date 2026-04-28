"""
    智能体构建
"""
import os
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

persist_dir = os.path.join(os.path.dirname(__file__), "law_all_data")

class FixedDashScopeEmbeddings(DashScopeEmbeddings):
    def embed_query(self, text: str) -> list[float]:
        # 强制将单一字符串包装成数组 [text]
        return self.embed_documents([text])[0]  # 按照处理多篇文档处理

str_parser = StrOutputParser()

prompt = "你是一个专业的法律咨询助手。请务必优先使用 retriever_tool 工具检索资料，并基于检索到的真实资料来回答用户的问题。"


if os.path.exists(persist_dir) and os.listdir(persist_dir):
    print("✨ 发现本地已存在向量数据库，直接加载数据，跳过耗时的 PDF 解析！")

    # 只需要初始化 Chroma 指向那个文件夹即可，它会自动加载里面的数据
    vector_store = Chroma(
        collection_name="rag",
        embedding_function=FixedDashScopeEmbeddings(),
        persist_directory=persist_dir
    )

else:
    # 使用相对于当前文件所在的准确路径，防止不同目录启动时找不到相对路径
    base_path = os.path.join(os.path.dirname(__file__), "data")
    loader = DirectoryLoader(
        path=base_path,
        loader_cls=TextLoader,  # 指定底层使用 TextLoader 来解析找到的文本文件
        show_progress=True, loader_kwargs={'encoding': 'utf-8'},  # 开启进度条（文件多的时候很实用，能看到解析进度）
        glob="**/*.txt"   # **/*.txt 表示匹配该文件夹及所有子文件夹下的所有 .txt 文件
    )

    documents = loader.load()

    # 文档切分
    text_spliters = RecursiveCharacterTextSplitter(
        chunk_size=300,  # 每个文档切分成多少个块
        chunk_overlap=5,  # 每个块之间的重叠长度
    )
    split_documents = text_spliters.split_documents(documents)

    # 初始化向量数据库
    vector_store = Chroma(
        collection_name="rag",  # 当前向量存储起个名字，类似数据库的表名
        # embedding_function=DashScopeEmbeddings(),  # 嵌入模型
        embedding_function=FixedDashScopeEmbeddings(),
        persist_directory=persist_dir  # 指定数据存放的文件夹
    )

    vector_store.add_documents(documents = split_documents)

retriever = vector_store.as_retriever(
    search_kwargs={"k": 1}
)

# 定义一个辅助函数，用于将检索到的多个 Document 对象的文本内容拼接成一段长字符串
def format_docs(docs_list):
    reference_text = '['
    for doc in docs_list:
        reference_text += doc.page_content
    reference_text += ']'
    return reference_text

# 定义一个工具，用于将用户的问题和检索到的文档作为输入，生成答案
@tool
def retriever_tool(query: str) -> str:
    """
    用于检索法律的知识库。
    当用户问及法律问题时，请务必调用此工具传入具体的查询问题(query)来获取参考资料。
    """
    docs = retriever.invoke(query)

    reference_text = format_docs(docs)
    return reference_text

def get_agent(deep_think: bool = False):
    model_name = "deepseek-reasoner" if deep_think else "deepseek-chat"
    print(f"Loading Model: {model_name}")  # 增加日志方便排查是否按条件切换

    current_model = ChatOpenAI(
        model=model_name,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )
    
    return create_react_agent(
        current_model,
        tools=[retriever_tool],
        prompt=prompt
    )

agent = get_agent(False)










