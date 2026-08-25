import os
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
try:
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
except Exception as e:
    print("初始化OpenAI客户端失败，请检查环境变量'DASHSCOPE_API_KEY'是否已设置。")
    print(f"错误信息:{e}")
    exit()

documents = [
    {
        "id": "doc1",
        "text": "迪士尼乐园的门票一经售出，原则上不予退换。但在特殊情况下，如恶劣天气导致园区关闭，可在官方指引下进行改期或退款。",
        "metadata": {"source": "official_faq_v1.pdf", "category": "退票政策", "author": "Admin"}
    },
    {
        "id": "doc2",
        "text": "购买“奇妙年卡”的用户，可以享受一年内多次入园的特权，并且在餐饮和购物时有折扣。",
        "metadata": {"source": "annual_pass_rules.docx", "category": "会员权益", "author": "MarketingDept"}
    },
    {
        "id": "doc3",
        "text": "对于在线购买的迪士尼门票，如果需要退票，必须在票面日期前48小时通过原购买渠道提交申请，并可能收取手续费。",
        "metadata": {"source": "online_policy.html", "category": "退票政策", "author": "E-commerceTeam"}
    },
    {
        "id": "doc4",
        "text": "园区内的“加勒比海盗”项目因年度维护，将于下周暂停开放。",
        "metadata": {"source": "maintenance_notice.txt", "category": "园区公告", "author": "OpsDept"}
    }
]

metadata_store = []
vectors_list = []
vector_ids = []

print("正在为文档生成向量...")

for i,doc in enumerate(documents):
    print("=============")
    print(i)
    print(doc["id"])
    try:
        completion = client.embeddings.create(
            model="text-embedding-v4",
            input=doc["text"],
            dimensions=1024,
            encoding_format="float"
        )

        vector = completion.data[0].embedding
        vectors_list.append(vector)
        metadata_store.append(doc)
        vector_ids.append(i)
        print(f"  - 已处理文档 {i+1}/{len(documents)}")
    except Exception as e:
        print(f"处理文档")
        continue
# 将向量列表转换为NumPy数组，FAISS需要这种格式
vectors_np = np.array(vectors_list).astype('float32')
vector_ids_np = np.array(vector_ids)

# Step4. 构建并填充 FAISS 索引
dimension = 1024  # 向量维度
k = 2  # 查找最近的3个邻居

# 创建一个基础的L2距离索引
index_flat_l2 = faiss.IndexFlatL2(dimension)

# 使用IndexIDMap来包装基础索引，能够映射我们自定义的ID
# 这就是关联向量和元数据的关键！
index = faiss.IndexIDMap(index_flat_l2)

# 将向量和它们对应的ID添加到索引中
index.add_with_ids(vectors_np, vector_ids_np)

print(f"\nFAISS 索引已成功创建，共包含 {index.ntotal} 个向量。")

# Step5. 执行搜索并检索元数据
query_text = "我想了解一下迪士尼门票的退款流程"
print(f"\n正在为查询文本生成向量: '{query_text}'")
try:
    query_completion = client.embeddings.create(
        model="text-embedding-v4",
        input=query_text,
        dimensions=1024,
        encoding_format="float"
    )
    query_vector = np.array([query_completion.data[0].embedding]).astype('float32')
    distances, retrieved_ids = index.search(query_vector, k)
    # Step6. 展示结果
    print("\n")
    print("------"*20)
    print("\n")
    for i in range(k):
        print(i)
        doc_id = retrieved_ids[0][i]
        if doc_id == -1:
            print(f"\n排名{i+1}")
            continue

        # 使用ID从我们的元数据存储中检索信息
        retrieved_doc = metadata_store[doc_id]

        print(f"\n--- 排名 {i + 1} (相似度得分/距离: {distances[0][i]:.4f}) ---")
        print(f"ID: {doc_id}")
        print(f"原始文本: {retrieved_doc['text']}")
        print(f"元数据: {retrieved_doc['metadata']}")


except Exception as e:
    print(f"生成查询向量失败: {e}")
