import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration
KNOWLEDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rag", "vector_index.json"))

# Setup Client
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
from core.config import settings
client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

def get_embedding(text):
    print(f"Embedding: {text[:30]}...")
    resp = client.embeddings.create(input=text, model=settings.LLM_EMBEDDING_MODEL)
    return resp.data[0].embedding

def build_index():
    print("开始构建便携式 RAG 索引...")
    if not LLM_API_KEY:
        print("错误: 请先在 .env 中设置 LLM_API_KEY")
        return

    documents = []
    # 1. Traverse knowledge-base
    for root, _, files in os.walk(KNOWLEDGE_DIR):
        for file in files:
            if file.endswith('.md') and file != 'README.md':
                path = os.path.join(root, file)
                print(f"正在处理: {file}")
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple chunking by paragraph for now or specific headers
                    chunks = content.split('###')
                    for chunk in chunks:
                        if chunk.strip():
                            documents.append(chunk.strip())
            elif file.endswith('.json'):
                path = os.path.join(root, file)
                print(f"正在读取题库: {file}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        q_str = f"岗位: {item.get('role', '通用')}\n题目: {item.get('question')}\n要点: {', '.join(item.get('expected_points', []))}"
                        documents.append(q_str)

    # 2. Generate Embeddings
    index_data = []
    for doc in documents:
        try:
            vec = get_embedding(doc)
            index_data.append({"content": doc, "embedding": vec})
        except Exception as e:
            print(f"Skip failed doc: {e}")

    # 3. Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"索引构建完成! 共 {len(index_data)} 条记录，保存在 {OUTPUT_FILE}")

if __name__ == "__main__":
    build_index()
