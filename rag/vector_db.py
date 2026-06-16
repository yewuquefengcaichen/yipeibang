"""
向量数据库初始化和操作
使用ChromaDB存储医疗知识
"""
import chromadb
from pathlib import Path
import json

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "medical_knowledge.json"

# 创建ChromaDB客户端
client = None
collection = None


def init_chromadb():
    """初始化ChromaDB"""
    global client, collection

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 创建或获取collection
    collection = client.get_or_create_collection(
        name="medical_knowledge",
        metadata={"description": "医疗健康知识库"}
    )

    print(f"ChromaDB initialized at: {CHROMA_DIR}")
    return collection


def ingest_knowledge():
    """导入知识库数据"""
    if collection is None:
        init_chromadb()

    # 读取知识库JSON
    if not KNOWLEDGE_FILE.exists():
        print(f"Knowledge file not found: {KNOWLEDGE_FILE}")
        return

    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        knowledge_items = json.load(f)

    print(f"Loading {len(knowledge_items)} knowledge items...")

    # 准备数据
    ids = []
    documents = []
    metadatas = []

    for i, item in enumerate(knowledge_items):
        ids.append(f"know_{i:04d}")
        documents.append(item['content'])
        metadatas.append({
            'category': item['category'],
            'tags': ','.join(item['tags']),
            'source': item['source']
        })

    # 批量插入（ChromaDB会自动生成嵌入向量）
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Successfully ingested {len(knowledge_items)} items into ChromaDB")
    print(f"Collection count: {collection.count()}")


def search_knowledge(query, top_k=5, category_filter=None):
    """搜索知识库"""
    if collection is None:
        init_chromadb()

    # 构建过滤条件
    where_filter = None
    if category_filter:
        where_filter = {"category": category_filter}

    # 向量搜索
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_filter
    )

    # 格式化结果
    formatted_results = []
    if results['documents'] and len(results['documents']) > 0:
        for i, doc in enumerate(results['documents'][0]):
            formatted_results.append({
                'content': doc,
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })

    return formatted_results


if __name__ == "__main__":
    # 初始化并导入数据
    init_chromadb()
    ingest_knowledge()

    # 测试搜索
    print("\n=== Testing Search ===")
    results = search_knowledge("空腹血糖正常范围", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['content'][:50]}...")
        print(f"   Category: {result['metadata']['category']}")
