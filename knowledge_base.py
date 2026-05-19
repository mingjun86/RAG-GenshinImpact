import os
import config_data as config
import hashlib
from langchain_community.vectorstores import FAISS  # 修改这行
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime


# 检查传入的md5字符串是否已经被处理过
def check_md5(md5_str: str):
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()
            if line == md5_str:
                return True
        return False


def save_md5(md5_str: str):
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str: str, encoding='utf-8'):
    str_bytes = input_str.encode(encoding=encoding)
    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    md5_hex = md5_obj.hexdigest()
    return md5_hex


class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok=True)

        self.embedding = DashScopeEmbeddings(model="text-embedding-v4")
        self.persist_directory = config.persist_directory
        self.vector_store = None
        self._load_or_create()

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

    def _load_or_create(self):
        """加载或创建向量存储"""
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vector_store = FAISS.load_local(
                    self.persist_directory,
                    self.embedding,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"加载失败: {e}，创建新数据库")
                self.vector_store = FAISS.from_texts(["初始化"], self.embedding)
        else:
            print("创建新的向量数据库")
            self.vector_store = FAISS.from_texts(["初始化"], self.embedding)

    def upload_by_str(self, data, filename):
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return "[跳过]内容已经存在知识库中"

        if len(data) > config.max_split_char_number:
            knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "小小"
        }

        self.vector_store.add_texts(
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks],
        )
        self.vector_store.save_local(self.persist_directory)

        save_md5(md5_hex)
        return "[成功]内容已经成功载入向量库"


if __name__ == '__main__':
    service = KnowledgeBaseService()
    r = service.upload_by_str("您好", "testfile")
    print(r)