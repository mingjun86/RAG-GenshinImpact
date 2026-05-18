import os
import config_data as config
import hashlib
import io
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

def extract_text_from_file(file_obj, file_ext: str) -> str:

    try:
        if file_ext == "txt":
            # TXT 文件直接解码
            return file_obj.getvalue().decode("utf-8")

        elif file_ext == "pdf":
            # PDF 文件解析
            try:
                from pypdf import PdfReader
            except ImportError:
                raise ImportError("请先安装 pypdf: pip install pypdf")

            pdf_reader = PdfReader(io.BytesIO(file_obj.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text

        elif file_ext == "docx":
            # Word 文件解析
            try:
                import docx
            except ImportError:
                raise ImportError("请先安装 python-docx: pip install python-docx")

            doc = docx.Document(io.BytesIO(file_obj.getvalue()))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text

        elif file_ext == "md":
            # Markdown 文件：提取纯文本
            content = file_obj.getvalue().decode("utf-8")
            try:
                import re
                # 简单的 Markdown 清理，移除标记符号
                content = re.sub(r'#{1,6}\s+', '', content)  # 移除标题标记 #
                content = re.sub(r'\*\*?(.*?)\*\*?', r'\1', content)  # 移除粗体/斜体标记
                content = re.sub(r'__(.*?)__', r'\1', content)  # 移除下划线标记
                content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)  # 移除链接标记 [text](url)
                content = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # 移除图片标记 ![alt](url)
                content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # 移除代码块标记
                content = re.sub(r'`(.*?)`', r'\1', content)  # 移除行内代码标记
            except:
                pass
            return content

        elif file_ext == "py":
            # Python 文件：提取代码内容
            return file_obj.getvalue().decode("utf-8")

        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    except Exception as e:
        raise Exception(f"解析文件时出错: {str(e)}")


def extract_text_from_multiple_files(files):
    """批量提取多个文件的文本内容"""
    all_text = ""
    for file in files:
        file_ext = file.name.split('.')[-1].lower()
        try:
            text = extract_text_from_file(file, file_ext)
            if text:
                all_text += f"\n\n--- 文件: {file.name} ---\n\n{text}"
        except Exception as e:
            print(f"解析文件 {file.name} 失败: {e}")
    return all_text



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

        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=DashScopeEmbeddings(model="text-embedding-v4"),
            persist_directory=config.persist_directory,
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

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
        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks],
        )

        save_md5(md5_hex)
        return "[成功]内容已经成功载入向量库"


if __name__ == '__main__':
    service = KnowledgeBaseService()
    r = service.upload_by_str("您好", "testfile")
    print(r)