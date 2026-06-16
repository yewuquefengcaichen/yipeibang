"""
简化的向量搜索服务
使用sentence-transformers，不依赖ChromaDB
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import json
from typing import List, Dict, Optional
import pickle

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "medical_knowledge.json"
EMBEDDINGS_FILE = DATA_DIR / "knowledge" / "embeddings.pkl"

# 全局变量
embedding_model = None
knowledge_base = []
embeddings_matrix = None


def init_embedding_model():
    """初始化嵌入模型"""
    global embedding_model
    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("Embedding model loaded!")
    return embedding_model


def load_knowledge_base():
    """加载知识库"""
    global knowledge_base
    if not knowledge_base:
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        print(f"Loaded {len(knowledge_base)} knowledge items")
    return knowledge_base


def generate_embeddings_for_knowledge(force_regenerate=False):
    """为知识库生成嵌入向量并缓存"""
    global embeddings_matrix

    # 检查缓存
    if EMBEDDINGS_FILE.exists() and not force_regenerate:
        print("Loading cached embeddings...")
        with open(EMBEDDINGS_FILE, 'rb') as f:
            embeddings_matrix = pickle.load(f)
        print(f"Loaded embeddings: shape {embeddings_matrix.shape}")
        return embeddings_matrix

    # 生成新的嵌入向量
    print("Generating embeddings for knowledge base...")
    model = init_embedding_model()
    knowledge = load_knowledge_base()

    texts = [item['content'] for item in knowledge]
    embeddings_matrix = model.encode(texts, show_progress_bar=True)

    # 缓存
    EMBEDDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(embeddings_matrix, f)
    print(f"Embeddings cached to {EMBEDDINGS_FILE}")

    return embeddings_matrix


def cosine_similarity(a, b):
    """计算余弦相似度"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search_knowledge_semantic(
    query: str,
    top_k: int = 5,
    category_filter: Optional[str] = None,
    score_threshold: float = 0.3
) -> List[Dict]:
    """语义搜索知识库"""
    global embeddings_matrix

    # 初始化
    model = init_embedding_model()
    knowledge = load_knowledge_base()

    if embeddings_matrix is None:
        embeddings_matrix = generate_embeddings_for_knowledge()

    # 生成查询向量
    query_embedding = model.encode([query])[0]

    # 计算相似度
    similarities = []
    for i, item in enumerate(knowledge):
        # 分类过滤
        if category_filter and item['category'] != category_filter:
            continue

        sim = cosine_similarity(query_embedding, embeddings_matrix[i])
        if sim >= score_threshold:
            similarities.append((i, sim))

    # 排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    similarities = similarities[:top_k]

    # 构建结果
    results = []
    for idx, score in similarities:
        item = knowledge[idx]
        results.append({
            'content': item['content'],
            'category': item['category'],
            'tags': item['tags'],
            'source': item['source'],
            'score': float(score)
        })

    return results


def hybrid_search_optimized(
    query: str,
    top_k: int = 5,
    category_filter: Optional[str] = None
) -> List[Dict]:
    """优化的混合搜索：语义搜索 + 关键词加权"""

    # 语义搜索
    semantic_results = search_knowledge_semantic(query, top_k * 2, category_filter, score_threshold=0.2)

    # 关键词加权
    query_lower = query.lower()
    for result in semantic_results:
        content_lower = result['content'].lower()

        # 关键词得分
        keyword_score = 0
        if query_lower in content_lower:
            keyword_score += 0.3  # 完全匹配

        # 单字匹配
        matched_chars = sum(1 for char in query_lower if char in content_lower)
        keyword_score += (matched_chars / len(query_lower)) * 0.1

        # 混合得分
        result['hybrid_score'] = result['score'] * 0.8 + keyword_score

    # 重新排序
    semantic_results.sort(key=lambda x: x['hybrid_score'], reverse=True)

    return semantic_results[:top_k]


if __name__ == "__main__":
    print("=== Simplified Vector Search Test ===\n")

    # 生成嵌入向量
    generate_embeddings_for_knowledge()

    # 测试语义搜索
    print("\n=== Testing Semantic Search ===")
    queries = [
        "空腹血糖正常范围是多少",
        "胸痛应该怎么办",
        "二甲双胍的副作用"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = search_knowledge_semantic(query, top_k=3)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.4f}")
            print(f"   Category: {result['category']}")
            print(f"   Content: {result['content'][:80]}...")

    # 测试混合搜索
    print("\n\n=== Testing Hybrid Search ===")
    query = "糖尿病患者饮食应该注意什么"
    print(f"\nQuery: {query}")
    results = hybrid_search_optimized(query, top_k=3)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Hybrid Score: {result['hybrid_score']:.4f} (Semantic: {result['score']:.4f})")
        print(f"   Category: {result['category']}")
        print(f"   Content: {result['content'][:100]}...")
