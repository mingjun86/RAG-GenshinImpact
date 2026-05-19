import os
import sys
from knowledge_base import KnowledgeBaseService, extract_text_from_file


def batch_upload(folder_path):
    """批量上传文件夹中的所有文件"""

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return

    print(f"📁 开始批量上传文件夹: {folder_path}")
    print("=" * 50)

    # 初始化知识库服务
    try:
        service = KnowledgeBaseService()
    except Exception as e:
        print(f"❌ 初始化知识库失败: {e}")
        return

    # 支持的文件类型
    supported_extensions = ['.txt', '.pdf', '.docx', '.md', '.py']

    success_count = 0
    skip_count = 0
    error_count = 0

    files = [f for f in os.listdir(folder_path)
             if os.path.splitext(f)[1].lower() in supported_extensions]

    if not files:
        print(f"⚠️ 文件夹中没有找到支持的文件类型: {supported_extensions}")
        return

    for filename in files:
        file_ext = os.path.splitext(filename)[1].lower()
        file_path = os.path.join(folder_path, filename)
        file_size = os.path.getsize(file_path) / 1024  # KB

        print(f"\n📄 正在处理: {filename} ({file_size:.2f} KB)")

        try:
            # 提取文本
            print(f"   📖 正在提取文本...")
            text = extract_text_from_file(file_path, file_ext[1:])

            if text and text.strip():
                print(f"   📝 文本长度: {len(text)} 字符")
                result = service.upload_by_str(text, filename)
                print(f"   {result}")

                if "成功" in result:
                    success_count += 1
                elif "跳过" in result:
                    skip_count += 1
            else:
                print(f"   ⚠️ 跳过: 无法提取内容或内容为空")
                error_count += 1

        except ImportError as e:
            print(f"   ❌ 缺少依赖库: {e}")
            print(f"   💡 请运行: pip install PyPDF2 python-docx")
            error_count += 1
            break

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            error_count += 1

    # 打印总结
    print("\n" + "=" * 50)
    print("📊 批量上传完成！")
    print(f"   ✅ 成功: {success_count} 个文件")
    print(f"   ⏭️ 跳过: {skip_count} 个文件（已存在）")
    print(f"   ❌ 失败: {error_count} 个文件")
    print("=" * 50)


if __name__ == "__main__":
    # 可以修改为你的 data 文件夹路径
    data_folder = "data"

    # 如果 data 文件夹不存在，创建它
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"📁 已创建文件夹: {data_folder}")
        print(f"💡 请将文件放入 {data_folder} 文件夹后重新运行")
    else:
        batch_upload(data_folder)