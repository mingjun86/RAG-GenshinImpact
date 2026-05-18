import streamlit as st
from knowledge_base import KnowledgeBaseService, extract_text_from_file
import time

st.title("知识库更新服务")

# 支持的文件类型
SUPPORTED_TYPES = ["txt", "pdf", "docx", "md", "py"]

uploader_file = st.file_uploader(
    f"请上传文件（支持格式：{', '.join(SUPPORTED_TYPES)}）",
    type=SUPPORTED_TYPES,
    accept_multiple_files=False,
)

if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()

if uploader_file is not None:
    # 获取文件信息
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size / 1024  # 单位kb
    file_ext = file_name.split('.')[-1].lower()

    st.subheader(f"文件名: {file_name}")
    st.write(f"格式: {file_type} | 大小: {file_size:.2f} KB")

    with st.spinner("正在解析并载入知识库中..."):
        time.sleep(1)

        # 根据文件类型提取文本内容
        text = extract_text_from_file(uploader_file, file_ext)

        if text and text.strip():
            result = st.session_state["service"].upload_by_str(text, file_name)
            if "成功" in result:
                st.success(result)
            else:
                st.info(result)
        else:
            st.error("无法提取文件内容，请检查文件格式是否正确")