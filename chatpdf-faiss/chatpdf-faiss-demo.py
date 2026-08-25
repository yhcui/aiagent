import os
import pickle
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from typing import List,Tuple
from langchain_community.vectorstores import FAISS
load_dotenv()
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")


def extract_text_with_page_numbers(pdf) -> Tuple[str, List[int]]:
    text = ""
    char_page_mapping = []
    for page_number, page in enumerate(pdf.pages, start=1):
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text
            char_page_mapping.extend([page_number] * len(extracted_text))
        else:
            print(f"No text found on page {page_number}.")
    print(char_page_mapping)
    return text, char_page_mapping

def process_text_with_splitter(text: str, char_page_mapping: List[int], save_path: str = None) -> FAISS:
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " ", ""],
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)

    embeddings = DashScopeEmbeddings(
        model = "text-embedding-v1",
        dashscope_api_key = DASHSCOPE_API_KEY
    )
    knowledgeBase = FAISS.from_texts(chunks, embeddings)
    page_info = {}
    current_pos = 0
    print("已从文本块创建知识库。")
    for chunk in chunks:
        chunk_start = current_pos
        chunk_end = current_pos + len(chunk)
        chunk_pages = char_page_mapping[chunk_start: chunk_end]
        if chunk_pages:
            page_counts = {}
            for page in chunk_pages:
                page_counts[page] = page_counts.get(page, 0) + 1
            most_common_page = max(page_counts, key=page_counts.get)
            page_info[chunk] = most_common_page
        else :
            page_info[chunk] = 1
        current_pos = chunk_end
    knowledgeBase.page_info = page_info
    print(f'页码映射完成，共 {len(page_info)} 个文本块')

    if save_path:
        os.makedirs(save_path, exist_ok=True)
        knowledgeBase.save_local(save_path)

        print(f"知识库已保存到 {save_path}")
        with open(os.path.join(save_path, "page_info.pkl"), "wb") as f:
            pickle.dump(page_info, f)
    return knowledgeBase

pdf_reader = PdfReader('./浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf')
text, char_page_mapping =  extract_text_with_page_numbers(pdf_reader)

print(f"提取的文本长度: {len(text)} 个字符。")
save_dir = "./vector_db"
knowledgeBase = process_text_with_splitter(text, char_page_mapping, save_path=save_dir)

from langchain_community.llms import Tongyi
llm = Tongyi(model_name="deepseek-v3", dashscope_api_key=DASHSCOPE_API_KEY)
query = "客户经理被投诉了，投诉一次扣多少分"

if query:
    docs = knowledgeBase.similarity_search(query, k=10)
    context = "\n\n".join([docs.page_content for docs in docs])
    prompt = f"""根据以下上下文回答问题:

    {context}

    问题: {query}"""

    response = llm.invoke(prompt)
    print(f"LLM Response: {response}")
    unique_pages = set()

    for doc in docs:
        text_content = getattr(doc, "page_content", "")
        source_page = knowledgeBase.page_info.get(text_content.strip(), "未知")
        if source_page not in unique_pages:
            print(f"文本块页码: {source_page}")


