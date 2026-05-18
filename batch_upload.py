import os
from knowledge_base import KnowledgeBaseService, extract_text_from_file


def batch_upload(folder_path):
    """批量上传文件夹中的所有文件"""
    service = KnowledgeBaseService()

    # 支持的文件类型
    supported_extensions = ['.txt', '.pdf', '.docx', '.md', '.py']

    for filename in os.listdir(folder_path):
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext in supported_extensions:
            file_path = os.path.join(folder_path, filename)
            print(f"正在处理: {filename}")

            try:
                # 读取文件
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                # 模拟文件对象
                class MockFile:
                    def __init__(self, name, content):
                        self.name = name
                        self._content = content

                    def getvalue(self):
                        return self._content

                mock_file = MockFile(filename, file_content)
                text = extract_text_from_file(mock_file, file_ext[1:])

                if text:
                    result = service.upload_by_str(text, filename)
                    print(f"  {result}")
                else:
                    print(f"  跳过: 无法提取内容")

            except Exception as e:
                print(f"  错误: {e}")

    print("批量上传完成！")


if __name__ == "__main__":
    batch_upload("data")  # 上传 data 文件夹中的所有文件