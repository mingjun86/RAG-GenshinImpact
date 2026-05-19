# MD5 记录文件
md5_path = "md5.text"

# 向量库配置
collection_name = "rag"
persist_directory = "./faiss_db"

# 文本分割配置
chunk_size = 700
chunk_overlap = 50
separators = ["\n\n", "\n", ".", "?", "!", "。", "？", "！", " ", ""]
max_split_char_number = 800  # 文本分割的阈值

# 检索配置
similarity_threshold = 5  # 检索返回匹配的文档数量


embedding_model_name = "text-embedding-v4"

# 对话模型
chat_model_name = "qwen-max"

# 会话配置
session_config = {
    "configurable": {
        "session_id": "user_001",
    }
}

# 生成配置
temperature = 0.1
max_tokens = 2048
streaming = True  # 启用流式输出