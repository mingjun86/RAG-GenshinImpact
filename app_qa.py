import streamlit as st
from rag import RagService
import config_data as config
import uuid
from PIL import Image
import os
import base64
from io import BytesIO
from datetime import datetime
from file_history_store import (
    get_conversation_list,
    save_conversation,
    load_conversation,
    delete_conversation,
    generate_title
)

# ========== 设置页面图标 ==========
current_dir = os.path.dirname(os.path.abspath(__file__))

main_icon_path = os.path.join(current_dir, "Image", "尼可.png")  # 主界面和侧边栏图标
ai_avatar_path = os.path.join(current_dir, "Image", "尼可有话要说.png")  # AI聊天头像
user_avatar_path = os.path.join(current_dir, "Image", "派蒙.jpg")  # 用户聊天头像

# 初始化变量
custom_icon = None
favicon = "🤖"
img_base64 = ""
img_base64_large = ""
ai_avatar_img = None  # 存储 AI 头像的 PIL Image 对象
user_avatar_img = None  # 存储用户头像的 PIL Image 对象
ai_avatar_base64 = ""
user_avatar_base64 = ""

# 加载主图标（用于页面、侧边栏、主标题）
try:
    if os.path.exists(main_icon_path):
        custom_icon = Image.open(main_icon_path)
        favicon = custom_icon

        # 将图片转换为 base64 编码（用于 CSS）
        buffered = BytesIO()
        custom_icon.save(buffered, format="PNG", quality=100, dpi=(300, 300))
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # 创建不同尺寸的高清图标
        icon_large = custom_icon.resize((160, 160), Image.Resampling.LANCZOS)
        buffered_large = BytesIO()
        icon_large.save(buffered_large, format="PNG", quality=100)
        img_base64_large = base64.b64encode(buffered_large.getvalue()).decode()

        print(f"成功加载主图标: {main_icon_path}, 尺寸: {custom_icon.size}")
    else:
        print(f"主图标文件不存在: {main_icon_path}，使用默认图标")
except Exception as e:
    print(f"加载主图标失败: {e}，使用默认图标")

# 加载 AI 聊天头像（作为 PIL Image 对象，用于 st.chat_message 的 avatar 参数）
try:
    if os.path.exists(ai_avatar_path):
        ai_avatar_img = Image.open(ai_avatar_path)
        # 同时生成 base64 用于 CSS（备用）
        ai_avatar_resized = ai_avatar_img.resize((40, 40), Image.Resampling.LANCZOS)
        buffered_ai = BytesIO()
        ai_avatar_resized.save(buffered_ai, format="PNG", quality=100)
        ai_avatar_base64 = base64.b64encode(buffered_ai.getvalue()).decode()
        print(f"成功加载AI头像: {ai_avatar_path}")
    else:
        print(f"AI头像文件不存在: {ai_avatar_path}，将使用主图标")
        if custom_icon:
            ai_avatar_img = custom_icon
            ai_temp = custom_icon.resize((40, 40), Image.Resampling.LANCZOS)
            buffered_ai = BytesIO()
            ai_temp.save(buffered_ai, format="PNG", quality=100)
            ai_avatar_base64 = base64.b64encode(buffered_ai.getvalue()).decode()
except Exception as e:
    print(f"加载AI头像失败: {e}")

# 加载用户聊天头像（作为 PIL Image 对象，用于 st.chat_message 的 avatar 参数）
try:
    if os.path.exists(user_avatar_path):
        user_avatar_img = Image.open(user_avatar_path)
        # 同时生成 base64 用于 CSS（备用）
        user_avatar_resized = user_avatar_img.resize((40, 40), Image.Resampling.LANCZOS)
        buffered_user = BytesIO()
        user_avatar_resized.save(buffered_user, format="PNG", quality=100)
        user_avatar_base64 = base64.b64encode(buffered_user.getvalue()).decode()
        print(f"成功加载用户头像: {user_avatar_path}")
    else:
        print(f"用户头像文件不存在: {user_avatar_path}，使用默认头像")
except Exception as e:
    print(f"加载用户头像失败: {e}")

st.set_page_config(
    page_title="尼可13号 - 《原神》提瓦特记录者",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>

    /* 副标题样式 */
    .subtitle {{
        text-align: center;
        background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 25%, #FF6B35 50%, #FF3B3B 75%, #D90000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 2rem;
        letter-spacing: 1px;
    }}

    /* 侧边栏样式 */
    .sidebar-header {{
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    /* 侧边栏欢迎语文字样式 */
    .welcome-text {{
        background: linear-gradient(135deg, #FF6B35 0%, #FF3B3B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
    }}

    /* 标题包装器 */
    .title-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-bottom: 0.5rem;
    }}

    /* 标题内容容器 */
    .title-content {{
        display: flex;
        align-items: center;
        gap: 25px;
    }}

    /* 高清图标容器 */
    .high-res-icon {{
        width: 80px;
        height: 80px;
        background-image: url('data:image/png;base64,{img_base64_large if custom_icon else ""}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        display: inline-block;
        transition: transform 0.3s ease;
        flex-shrink: 0;
    }}

    /* 主标题文字样式 */
    .main-title-text {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
        padding: 0;
        display: inline-block;
        white-space: nowrap;
    }}

    /* 主图标悬停效果 */
    .high-res-icon:hover {{
        transform: scale(1.1);
        transition: transform 0.3s ease;
    }}
    /* 对话头像图标悬停效果 */
    .stChatMessage [data-testid="avatar"]:hover {{
        transform: scale(1.1) !important;
        transition: transform 0.3s ease !important;
        filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.4)) !important;
    }}
    /* 优化头像图片渲染质量 */
    .stChatMessage [data-testid="avatar"] img {{
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
        image-rendering: pixelated;
        image-rendering: auto;
        -webkit-font-smoothing: antialiased;
    }}

    /* 对话列表项样式 */
    .conversation-item {{
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .conversation-item:hover {{
        background-color: #f0f2f6;
    }}

    /* 响应式设计 */
    @media (max-width: 768px) {{
        .high-res-icon {{
            width: 60px;
            height: 60px;
        }}
        .main-title-text {{
            font-size: 2rem;
        }}
        .title-content {{
            gap: 15px;
        }}
    }}

    /* 侧边栏图标 */
    .sidebar-high-res-icon {{
        width: 50px;
        height: 50px;
        background-image: url('data:image/png;base64,{img_base64 if custom_icon else ""}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        image-rendering: -webkit-optimize-contrast;
        display: inline-block;
    }}

    /* 统计卡片样式 */
    .stat-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }}

    .stat-number {{
        font-size: 2rem;
        font-weight: bold;
    }}

    .stat-label {{
        font-size: 0.8rem;
        opacity: 0.9;
    }}

    /* 消息气泡样式优化 */
    [data-testid="stChatMessage"] {{
        border-radius: 15px;
        margin: 10px 0;
    }}

    /* 用户消息样式 */
    [data-testid="stChatMessage"][data-testid="user"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }}

    /* 隐藏默认的 Streamlit 品牌标识 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* 按钮悬停效果 */
    .stButton > button {{
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    /* 加载动画 */
    @keyframes pulse {{
        0% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
        100% {{ opacity: 0.6; }}
    }}
    .loading-text {{
        animation: pulse 1.5s infinite;
    }}

    /* 流式输出光标动画 */
    @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0; }}
    }}
    .streaming-cursor {{
        animation: blink 1s infinite;
        display: inline-block;
        width: 2px;
        height: 1.2em;
        background-color: #667eea;
        margin-left: 2px;
        vertical-align: middle;
    }}
</style>
""", unsafe_allow_html=True)

# ========== 初始化会话状态（对话保存相关） ==========
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "conversation_messages" not in st.session_state:
    st.session_state.conversation_messages = {}

if "rag" not in st.session_state:
    with st.spinner("正在初始化尼可13号..."):
        st.session_state.rag = RagService()

# ========== 侧边栏配置 ==========
with st.sidebar:
    st.markdown('<div class="sidebar-header">✨ 尼可13号</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        if custom_icon:
            st.markdown('<div class="sidebar-high-res-icon"></div>', unsafe_allow_html=True)
        else:
            st.markdown("🤖", unsafe_allow_html=True)
    with col2:
        st.markdown("""
           <div style="display: flex; align-items: center; height: 100%; min-height: 50px;">
               <span class="welcome-text">🔥魔法记忆泡泡的编导师</span>
           </div>
           """, unsafe_allow_html=True)

    st.markdown("---")

    # ========== 新建对话按钮 ==========
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("➕ 新建对话", use_container_width=True):
            # 保存当前对话
            if st.session_state.current_conversation_id and st.session_state.current_conversation_id in st.session_state.conversation_messages:
                messages = st.session_state.conversation_messages[st.session_state.current_conversation_id]
                if messages:
                    title = generate_title(messages)
                    save_conversation(st.session_state.current_conversation_id, title, messages)

            # 创建新对话
            new_id = str(uuid.uuid4())[:8]
            st.session_state.current_conversation_id = new_id
            st.session_state.conversation_messages[new_id] = [
                {"role": "assistant", "content": "迷途的旅人啊~~让我来为您指引方向吧~"}]

            # 更新 LangChain 的 session_id
            config.session_config["configurable"]["session_id"] = f"user_{new_id}"
            st.rerun()

    with col2:
        # 刷新按钮
        if st.button("🔄", help="刷新对话列表"):
            st.rerun()

    st.markdown("---")

    # ========== 历史对话列表 ==========
    st.markdown("### 💬 历史对话")

    conversations = get_conversation_list()

    if conversations:
        for conv in conversations:
            col1, col2 = st.columns([4, 1])
            with col1:
                # 显示对话项
                if st.button(
                        f"📝 {conv['title']}",
                        key=f"conv_{conv['id']}",
                        use_container_width=True,
                        help=f"创建于: {conv['created_at']}\n消息数: {conv['message_count']}"
                ):
                    # 保存当前对话
                    if st.session_state.current_conversation_id and st.session_state.current_conversation_id in st.session_state.conversation_messages:
                        current_messages = st.session_state.conversation_messages[
                            st.session_state.current_conversation_id]
                        if current_messages:
                            title = generate_title(current_messages)
                            save_conversation(st.session_state.current_conversation_id, title, current_messages)

                    # 加载选中的对话
                    conv_data = load_conversation(conv["id"])
                    if conv_data:
                        st.session_state.current_conversation_id = conv["id"]
                        st.session_state.conversation_messages[conv["id"]] = conv_data["messages"]
                        config.session_config["configurable"]["session_id"] = f"user_{conv['id']}"
                        st.rerun()

            with col2:
                # 删除按钮
                if st.button("🗑️", key=f"del_{conv['id']}", help="删除对话"):
                    delete_conversation(conv["id"])
                    # 如果删除的是当前对话，清空当前对话
                    if st.session_state.current_conversation_id == conv["id"]:
                        st.session_state.current_conversation_id = None
                        if conv["id"] in st.session_state.conversation_messages:
                            del st.session_state.conversation_messages[conv["id"]]
                    st.rerun()
    else:
        st.caption("暂无历史对话，点击「新建对话」开始")

    st.markdown("---")

    # ========== 清空所有对话按钮 ==========
    if st.button("🗑️ 清空所有历史", use_container_width=True):
        import shutil

        if os.path.exists("saved_conversations"):
            shutil.rmtree("saved_conversations")
        st.session_state.conversation_messages = {}
        st.session_state.current_conversation_id = None
        st.rerun()

    st.markdown("---")

    # ========== 原有会话管理按钮 ==========
    if st.button("🗑️ 清空当前对话", use_container_width=True):
        if st.session_state.current_conversation_id:
            st.session_state.conversation_messages[st.session_state.current_conversation_id] = [
                {"role": "assistant", "content": "故事告一段落，是否想听新的故事？"}
            ]
            st.rerun()

# ========== 主界面 ==========
if custom_icon:
    st.markdown(f'''
    <div class="title-wrapper">
        <div class="title-content">
            <div class="high-res-icon"></div>
            <div class="main-title-text">尼可13号</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown('<div class="main-title">尼可13号</div>', unsafe_allow_html=True)

st.markdown('<div class="subtitle">有问非必答 —— 提瓦特记录者</div>', unsafe_allow_html=True)

st.divider()

# ========== 如果没有当前对话，创建默认对话 ==========
if st.session_state.current_conversation_id is None:
    st.session_state.current_conversation_id = str(uuid.uuid4())[:8]
    st.session_state.conversation_messages[st.session_state.current_conversation_id] = [
        {"role": "assistant", "content": "迷途的旅人啊~~让我来为您指引方向吧~"}
    ]
    config.session_config["configurable"]["session_id"] = f"user_{st.session_state.current_conversation_id}"

# 获取当前对话的消息
current_messages = st.session_state.conversation_messages.get(st.session_state.current_conversation_id, [])

# ========== 聊天区域 - 使用 avatar 参数显示自定义头像 ==========
chat_container = st.container()

with chat_container:
    for idx, message in enumerate(current_messages):
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar=ai_avatar_img if ai_avatar_img else None):
                if idx > 0:
                    st.caption("大天使尼可 · 刚刚")
                st.write(message["content"])
        else:  # user
            with st.chat_message("user", avatar=user_avatar_img if user_avatar_img else None):
                if idx > 0:
                    st.caption("用户 · 刚刚")
                st.write(message["content"])

# ========== 输入区域 ==========
prompt = st.chat_input("💬 输入你想了解的故事...")

st.markdown("### 🔍 快捷提问")
quick_questions = [
    "蒙德是怎样建成的？",
    "简述已知提瓦特的重大历史事件？",
    "稻妻的雷电将军有什么故事？",
    "坎瑞亚是什么？"
]

cols = st.columns(len(quick_questions))
for i, q in enumerate(quick_questions):
    with cols[i]:
        if st.button(q, use_container_width=True):
            prompt = q

if prompt:
    # 显示用户消息（使用用户头像）
    with st.chat_message("user", avatar=user_avatar_img if user_avatar_img else None):
        st.caption("用户 · 刚刚")
        st.write(prompt)
    current_messages.append({"role": "user", "content": prompt})

    # 获取 AI 回复（使用 AI 头像）
    with st.chat_message("assistant", avatar=ai_avatar_img if ai_avatar_img else None):
        st.caption("大天使尼可 · 回忆中...")

        response_placeholder = st.empty()
        full_response = ""

        try:
            res_stream = st.session_state.rag.chain.stream(
                {"input": prompt},
                config.session_config
            )

            for chunk in res_stream:
                if chunk:
                    full_response += chunk
                    response_placeholder.markdown(full_response + '<span class="streaming-cursor"></span>',
                                                  unsafe_allow_html=True)

            response_placeholder.markdown(full_response)

        except Exception as e:
            error_msg = f"啊哦，被天理制裁了呢~ {str(e)}"
            response_placeholder.markdown(error_msg)
            full_response = error_msg

    current_messages.append({"role": "assistant", "content": full_response})

    # 自动保存对话
    save_conversation(st.session_state.current_conversation_id, generate_title(current_messages), current_messages)

    st.rerun()