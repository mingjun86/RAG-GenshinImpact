# vector_stores.py - 使用 FAISS 替代 Chroma
from langchain_community.vectorstores import FAISS
import config_data as config
import os


class VectorStoreService(object):
    def __init__(self, embedding):
        self.embedding = embedding
        self.persist_directory = config.persist_directory
        self.vector_store = None
        self._load_or_create()

    def _load_or_create(self):
        """加载或创建向量存储"""
        os.makedirs(self.persist_directory, exist_ok=True)

        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vector_store = FAISS.load_local(
                    self.persist_directory,
                    self.embedding,
                    allow_dangerous_deserialization=True
                )
                print(f"已加载向量数据库，包含 {self.vector_store.index.ntotal} 个向量")
            except Exception as e:
                print(f"加载失败: {e}，创建新数据库")
                self.vector_store = FAISS.from_texts(
                    ["初始化知识库，请上传文档"],
                    self.embedding
                )
        else:
            print("创建新的向量数据库")
            self.vector_store = FAISS.from_texts(
                ["初始化知识库，请上传文档"],
                self.embedding
            )

    def add_texts(self, texts, metadatas):
        """添加文本到向量存储"""
        self.vector_store.add_texts(texts, metadatas)
        self.vector_store.save_local(self.persist_directory)
        print(f"已添加 {len(texts)} 个文档片段")

    def get_retriever(self, k=None):
        """获取检索器"""
        if k is None:
            k = config.similarity_threshold
        return self.vector_store.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    from langchain_community.embeddings import DashScopeEmbeddings

    retriever = VectorStoreService(DashScopeEmbeddings(model="text-embedding-v4")).get_retriever()
    res = retriever.invoke("测试")
    print(res)