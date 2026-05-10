import os
import json
import glob

# 注意：运行此脚本需要安装以下依赖：
# pip install chromadb langchain langchain-community langchain-huggingface sentence-transformers

try:
    from langchain_community.document_loaders import JSONLoader, TextLoader
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain.schema import Document
except ImportError:
    # 兼容处理或者不退出，依然要保证用到 Document 时能引入
    from langchain_core.documents import Document
    print("使用了备用导入处理...")

KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge-base"))
VECTOR_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "rag", "chroma_db"))

def load_json_questions(filepath):
    """
    加载 JSON 题库，并将其转换为 LangChain Document 对象。
    将 expected_points 和评价标准合并为 document 内容。
    """
    documents = []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            content = f"题目: {item.get('question')}\n"
            content += f"回答要点: {', '.join(item.get('expected_points', []))}\n"
            content += f"满分标准: {item.get('evaluation_criteria', {}).get('excellent', '')}\n"
            
            metadata = {
                "source": filepath,
                "question_id": item.get('id', ''),
                "difficulty": item.get('difficulty', ''),
                "category": item.get('category', '')
            }
            documents.append(Document(page_content=content, metadata=metadata))
    return documents

def load_markdown_knowledge(filepath):
    """加载 Markdown 知识点并切块"""
    loader = TextLoader(filepath, encoding='utf-8')
    docs = loader.load()
    # 使用文本分割器切片
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_documents(docs)

def build_vector_db():
    print("开始构建 RAG 向量数据库...")
    all_documents = []

    # 1. 递归读取所有 JSON 题库 和 Markdown 知识库
    for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.json'):
                print(f"正在处理题库: {file}")
                all_documents.extend(load_json_questions(filepath))
            elif file.endswith('.md') and file != 'README.md':
                print(f"正在处理知识点: {file}")
                all_documents.extend(load_markdown_knowledge(filepath))

    if not all_documents:
        print("未找到任何有效文档！")
        return

    print(f"共加载 {len(all_documents)} 个文档切片，正在进行向量化入库...")
    
    # 2. 初始化开源免费的 Embedding 模型 (可根据后端实际情况替换为 OpenAI/阿里云 等商业大模型相关方案)
    # 使用 BAAI/bge-small-zh-v1.5 是非常好的中文开源嵌入模型
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

    # 3. 创建 Chroma 本地向量数据库并持久化
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )
    
    print(f"向量数据库已成功构建，保存在 {VECTOR_DB_DIR}")

if __name__ == "__main__":
    build_vector_db()
