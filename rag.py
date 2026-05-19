from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.runnables import RunnableWithMessageHistory

from knowledge_base import KnowledgeBaseService
import config_data as config
from file_history_store import get_history


def print_prompt(prompt):
    print("*" * 20)
    if hasattr(prompt, 'to_string'):
        print(prompt.to_string())
    else:
        print(prompt)
    print("*" * 20)
    return prompt


class RagService(object):
    def __init__(self):
        print("正在初始化知识库服务...")
        self.knowledge_service = KnowledgeBaseService()

        # ========== 关键修改 1: 修改 Prompt 模板 ==========
        # 将 MessagesPlaceholder("history") 改为普通的 {history} 变量
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """你是在异世界提瓦特、存活数千年的天使、名为尼可·莱恩，并且熟知提瓦特的历史。提瓦特是游戏《原神》里的世界。参考历史资料：{context}，所有的术语和专有名词都只能来自该资料

## 回答格式要求（必须遵守）：
1. **必须使用标题和分类**来组织回答
2. 使用二级标题（##）标记主要分类，必须有序号，以便更清晰地展示内容，
3. 使用三级标题（###）标记子分类
4. 主标题不要加序号，即只有一个标题的此级别的标题不要加序号
5. 重要信息使用 **加粗** 突出
6. 并列内容使用 - 列表形式呈现

示例格式：
#主标题（就一个或两个，不加序号）
## 一、主要分类一(加序号)
### 子分类
- 关键词（不要把“关键词”这三个字写出来，不要出现“关键词”这三个字）：xxx详细说明...
- 关键词：xxx详细说明...
-...
...

## 二、主要分类二
..."""),
                ("system", "以下是我们的对话历史：\n{history}"),  # 改这里：使用普通变量
                ("user", "请回答用户问题：{input}")
            ]
        )

        self.chat_model = ChatTongyi(
            model=config.chat_model_name,
            temperature=config.temperature,
            streaming=getattr(config, 'streaming', True),
            max_tokens=config.max_tokens,
        )
        self.chain = self.__get_chain()

    def __get_chain(self):
        retriever = self.knowledge_service.get_retriever()

        def format_document(docs):
            if not docs:
                return "无相关记录文献"
            formatted_str = ""
            for i, doc in enumerate(docs, 1):
                formatted_str += f"文档片段{i}: {doc.page_content}\n"
                formatted_str += f"来源：{doc.metadata.get('source', '未知')}\n\n"
            return formatted_str

        # ========== 关键修改 2: 添加获取和格式化历史的函数 ==========
        def get_and_format_history(config_dict):
            """根据 session_id 获取历史消息，并格式化为字符串"""
            # 从 config 中获取 session_id
            session_id = config_dict.get("configurable", {}).get("session_id", "user_001")
            # 使用 get_history 函数获取历史记录对象
            history_obj = get_history(session_id)
            # 获取历史消息列表 (LangChain 的 BaseMessage 对象列表)
            messages = history_obj.messages

            # 格式化为字符串
            if not messages:
                return "暂无历史对话。"

            history_str = ""
            for msg in messages:
                if msg.type == "human":
                    history_str += f"用户: {msg.content}\n"
                elif msg.type == "ai":
                    history_str += f"天使尼可: {msg.content}\n"
            return history_str

        # 构建 RAG 链
        chain = (
                {
                    # 从输入中提取用户问题
                    "input": RunnablePassthrough(),
                    # 检索相关文档
                    "context": RunnableLambda(lambda x: x.get("input", "")) | retriever | format_document,
                    # ========== 关键修改 3: 在链中获取历史记录 ==========
                    "history": RunnableLambda(lambda x: get_and_format_history(config.session_config))
                }
                | self.prompt_template
                | print_prompt
                | self.chat_model
                | StrOutputParser()
        )

        # 如果需要使用 RunnableWithMessageHistory 来管理历史（自动保存）
        # 这里的 RunnableWithMessageHistory 主要用来在每次调用后自动保存新的对话
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",  # 这个参数在 chain 内部没用，但为了 RunnableWithMessageHistory 必须提供
        )

        return conversation_chain


if __name__ == "__main__":
    session_config = {
        "configurable": {
            "session_id": "user_001",
        }
    }

    print("测试 RAG 服务...")
    rag = RagService()
    try:
        # 测试时也需要传入 config
        res = rag.chain.invoke({"input": "简述蒙德的建成历史"}, session_config)
        print("\n最终回答：")
        print(res)
    except Exception as e:
        print(f"错误: {e}")