import streamlit as st
from rag import RagService
import config_data as config
import uuid

st.set_page_config(
    page_title="尼可13号 - 《原神》提瓦特记录者",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    /* 副标题样式 */
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }

    /* 侧边栏样式 */
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }

    /* 统计卡片样式 */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: bold;
    }

    .stat-label {
        font-size: 0.8rem;
        opacity: 0.9;
    }

    /* 消息气泡样式优化 */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        margin: 10px 0;
    }

    /* 用户消息样式 */
    [data-testid="stChatMessage"][data-testid="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* 隐藏默认的 Streamlit 品牌标识 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 按钮悬停效果 */
    .stButton > button {
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* 加载动画 */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .loading-text {
        animation: pulse 1.5s infinite;
    }

    /* 流式输出光标动画 */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    .streaming-cursor {
        animation: blink 1s infinite;
        display: inline-block;
        width: 2px;
        height: 1.2em;
        background-color: #667eea;
        margin-left: 2px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# ========== 侧边栏配置 ==========
with st.sidebar:
    st.markdown('<div class="sidebar-header">✨ 尼可13号</div>', unsafe_allow_html=True)

    # 头像和欢迎语
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("🤖", unsafe_allow_html=True)
    with col2:
        st.markdown("**魔法记忆泡泡的编导师**")

    st.markdown("---")

    # 会话控制
    st.markdown("### 💬 会话管理")

    # 新建会话按钮
    if st.button("➕ 新建会话", use_container_width=True):
        st.session_state["message"] = [{"role": "assistant", "content": "你好呀~旅行者，有什么想听的故事吗?"}]
        if "rag" in st.session_state:
            # 生成新的 session_id
            config.session_config["configurable"]["session_id"] = f"user_{uuid.uuid4().hex[:8]}"
        st.rerun()

    # 清空对话按钮
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state["message"] = [{"role": "assistant", "content": "故事告一段落，是否想听新的故事？"}]
        st.rerun()

    st.markdown("---")

# ========== 主界面 ==========
# 标题区域
st.markdown('<div class="main-title">🤖 尼可13号 </div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">有问非必答 —— 提瓦特记录者</div>', unsafe_allow_html=True)

# 分割线
st.divider()

# 初始化会话状态
if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "迷途的旅人啊~~让我来为您指引方向吧~"}]

if "rag" not in st.session_state:
    with st.spinner("正在初始化尼可13号..."):
        st.session_state["rag"] = RagService()

# ========== 聊天区域 ==========
# 使用容器包裹聊天历史
chat_container = st.container()

with chat_container:
    # 显示历史对话
    for idx, message in enumerate(st.session_state["message"]):
        with st.chat_message(message["role"]):
            # 为消息添加时间戳（可选）
            if idx > 0:  # 第一条消息不显示时间
                st.caption(f"{'用户' if message['role'] == 'user' else '天使尼可'} · 刚刚")
            st.write(message["content"])

# ========== 输入区域 ==========
# 用户输入栏
prompt = st.chat_input("💬 输入你想了解的故事...")

# 快捷问题按钮
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
    # 在页面输出用户的提问
    with st.chat_message("user"):
        st.caption("用户 · 刚刚")
        st.write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    # 获取 AI 回复
    with st.chat_message("assistant"):
        st.caption("大天使尼可 · 回忆中...")

        # 创建一个空的响应占位符
        response_placeholder = st.empty()
        full_response = ""

        try:
            # 获取流式响应
            res_stream = st.session_state["rag"].chain.stream(
                {"input": prompt},
                config.session_config
            )

            # 逐块输出，实现流式显示
            for chunk in res_stream:
                if chunk:
                    full_response += chunk
                    # 实时更新显示，带光标闪烁效果
                    response_placeholder.markdown(full_response + '<span class="streaming-cursor"></span>',
                                                  unsafe_allow_html=True)

            # 最终显示完整内容（去掉光标）
            response_placeholder.markdown(full_response)

        except Exception as e:
            error_msg = f"啊哦，被天理制裁了呢~ {str(e)}"
            response_placeholder.markdown(error_msg)
            full_response = error_msg

    # 保存到历史记录
    st.session_state["message"].append({"role": "assistant", "content": full_response})

    # 自动滚动到底部
    st.rerun()