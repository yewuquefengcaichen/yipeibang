"""
ChromaDB向量数据库服务
使用sentence-transformers生成嵌入向量
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "medical_knowledge.json"

# 全局变量
client = None
collection = None
embedding_model = None


def init_chromadb():
    """初始化ChromaDB和嵌入模型"""
    global client, collection, embedding_model

    # 创建目录
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化嵌入模型（使用中文优化模型）
    print("Loading embedding model...")
    embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("Embedding model loaded!")

    # 初始化ChromaDB
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # 创建或获取collection
    try:
        collection = client.get_collection(name="medical_knowledge")
        print(f"Loaded existing collection: {collection.count()} items")
    except:
        collection = client.create_collection(
            name="medical_knowledge",
            metadata={"description": "医疗健康知识库"}
        )
        print("Created new collection")

    return collection


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """生成文本嵌入向量"""
    if embedding_model is None:
        init_chromadb()

    embeddings = embedding_model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def ingest_knowledge(force_reload=False):
    """导入知识库数据到ChromaDB"""
    if collection is None:
        init_chromadb()

    # 检查是否已有数据
    if collection.count() > 0 and not force_reload:
        print(f"Collection already has {collection.count()} items, skipping ingestion")
        return

    # 清空collection（如果强制重载）
    if force_reload and collection.count() > 0:
        client.delete_collection("medical_knowledge")
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
    embeddings_list = []

    # 批量生成嵌入向量
    texts = [item['content'] for item in knowledge_items]
    print("Generating embeddings...")
    embeddings_list = generate_embeddings(texts)

    for i, item in enumerate(knowledge_items):
        ids.append(f"know_{i:04d}")
        documents.append(item['content'])
        metadatas.append({
            'category': item['category'],
            'tags': ','.join(item['tags']),
            'source': item['source']
        })

    # 批量插入
    batch_size = 10
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_embeds = embeddings_list[i:i+batch_size]

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=batch_embeds
        )
        print(f"Ingested {min(i+batch_size, len(ids))}/{len(ids)} items")

    print(f"Successfully ingested {len(knowledge_items)} items into ChromaDB")
    print(f"Collection count: {collection.count()}")


def search_knowledge_vector(
    query: str,
    top_k: int = 5,
    category_filter: Optional[str] = None
) -> List[Dict]:
    """使用向量搜索知识库"""
    if collection is None:
        init_chromadb()

    # 生成查询向量
    query_embedding = generate_embeddings([query])[0]

    # 构建过滤条件
    where_filter = None
    if category_filter:
        where_filter = {"category": category_filter}

    # 向量搜索
    results = collection.query(
        query_embeddings=[query_embedding],
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
                'distance': results['distances'][0][i] if 'distances' in results else None,
                'score': 1 - results['distances'][0][i] if 'distances' in results else 1.0
            })

    return formatted_results


def hybrid_search(
    query: str,
    top_k: int = 5,
    category_filter: Optional[str] = None,
    use_vector: bool = True
) -> List[Dict]:
    """混合搜索：向量搜索 + 关键词匹配"""

    if use_vector:
        # 使用向量搜索
        vector_results = search_knowledge_vector(query, top_k * 2, category_filter)

        # 重新排序：结合向量相似度和关键词匹配
        for result in vector_results:
            keyword_score = 0
            content = result['content'].lower()
            query_lower = query.lower()

            # 完整匹配加分
            if query_lower in content:
                keyword_score += 10

            # 单字匹配加分
            for char in query_lower:
                if char in content:
                    keyword_score += 0.5

            # 综合得分
            result['hybrid_score'] = result['score'] * 0.7 + (keyword_score / 20) * 0.3

        # 按混合得分排序
        vector_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return vector_results[:top_k]

    else:
        # 降级到简单文本搜索
        from services.rag_service import search_knowledge as simple_search
        return simple_search(query, top_k, category_filter)


if __name__ == "__main__":
    # 测试代码
    print("=== ChromaDB Vector Database Test ===\n")

    # 初始化并导入数据
    init_chromadb()
    ingest_knowledge(force_reload=False)

    # 测试搜索
    print("\n=== Testing Vector Search ===")
    query = "空腹血糖正常范围"
    print(f"\nQuery: {query}")
    results = search_knowledge_vector(query, top_k=3)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   Content: {result['content'][:80]}...")
        print(f"   Category: {result['metadata']['category']}")

    # 测试混合搜索
    print("\n\n=== Testing Hybrid Search ===")
    query = "胸痛应该怎么办"
    print(f"\nQuery: {query}")
    results = hybrid_search(query, top_k=3)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Hybrid Score: {result['hybrid_score']:.4f}")
        print(f"   Content: {result['content'][:80]}...")
        print(f"   Category: {result['metadata']['category']}")
