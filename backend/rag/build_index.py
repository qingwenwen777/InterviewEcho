import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from core.config import settings

load_dotenv()

KNOWLEDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rag", "vector_index.json"))
MAX_EMBEDDING_CHARS = int(os.getenv("RAG_EMBEDDING_MAX_CHARS", "7000"))
CHUNK_OVERLAP_CHARS = int(os.getenv("RAG_CHUNK_OVERLAP_CHARS", "300"))


def split_for_embedding(text, max_chars=MAX_EMBEDDING_CHARS, overlap=CHUNK_OVERLAP_CHARS):
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = []
    current_len = 0
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]

    def flush_current():
        nonlocal current, current_len
        if current:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_len = 0

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            flush_current()
            step = max(1, max_chars - overlap)
            for start in range(0, len(paragraph), step):
                segment = paragraph[start:start + max_chars].strip()
                if segment:
                    chunks.append(segment)
            continue

        separator_len = 2 if current else 0
        if current and current_len + separator_len + len(paragraph) > max_chars:
            flush_current()
            separator_len = 0

        current.append(paragraph)
        current_len += separator_len + len(paragraph)

    flush_current()
    return chunks


def get_embedding(client, text):
    print(f"Embedding: {text[:30]}...")
    resp = client.embeddings.create(input=text, model=settings.LLM_EMBEDDING_MODEL)
    return resp.data[0].embedding


def collect_documents():
    documents = []
    for root, _, files in os.walk(KNOWLEDGE_DIR):
        for file in sorted(files):
            path = os.path.join(root, file)
            if file.endswith(".md") and file != "README.md":
                print(f"Processing: {file}")
                with open(path, "r", encoding="utf-8") as f:
                    for chunk in f.read().split("###"):
                        documents.extend(split_for_embedding(chunk))
            elif file.endswith(".json"):
                print(f"Reading question bank: {file}")
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        q_str = (
                            f"Role: {item.get('role', 'general')}\n"
                            f"Question: {item.get('question')}\n"
                            f"Key points: {', '.join(item.get('expected_points', []))}"
                        )
                        documents.extend(split_for_embedding(q_str))
    return documents


def build_index():
    print("Building portable RAG index...")
    if not settings.LLM_API_KEY:
        print("Error: please set LLM_API_KEY in .env")
        return

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
    index_data = []
    for doc in collect_documents():
        try:
            vec = get_embedding(client, doc)
            index_data.append({"content": doc, "embedding": vec})
        except Exception as e:
            print(f"Skip failed doc: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Index build complete. {len(index_data)} records saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_index()
