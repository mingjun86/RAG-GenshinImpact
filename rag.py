from xml.dom.minidom import Document

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda

from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi

from file_history_store import get_history

def print_prompt(prompt):
    print("*"*20)
    print(prompt.to_string())
    print("*"*20)

    return prompt

class RagService(object):
    def __init__(self):
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name),
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """你是在提瓦特存活数千年的天使，并且熟知提瓦特的历史。参考历史资料：{context}

        ## 回答格式要求（必须遵守）：
        1. **必须使用标题和分类，添加序号**来组织回答
        2. 使用二级标题（##）标记主要分类
        3. 使用三级标题（###）标记子分类
        4. 重要信息使用 **加粗** 突出
        5. 并列内容使用 - 列表形式呈现

        示例格式：
        ## 主要分类一
        - 要点1：xxx
        - 要点2：xxx

        ### 子分类
        详细说明...

        ## 主要分类二
        ..."""),
                ("system", "并且我提供用户的对话历史，如下"),
                MessagesPlaceholder("history"),
                ("user", "请回答用户问题：{input}")
            ]
        )
        # 关键修改：设置 streaming=True 启用流式输出
        self.chat_model = ChatTongyi(
            model=config.chat_model_name,
            temperature=config.temperature,
            streaming=True,  # 启用流式输出
            max_tokens=config.max_tokens,
        )
        self.chain = self.__get_chain()

    #
    def __get_chain(self):
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关记录文献"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段:{doc.page_content}\n文档元数据：{doc.metadata}\n\n"

            return formatted_str

        def format_for_retriever(value: dict) -> str:
            return value["input"]

        def format_for_prompt_template(value):
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["history"] = value["input"]["history"]
            new_value["context"] = value["context"]
            return new_value

        chain = (
            {"input": RunnablePassthrough(), "context": RunnableLambda(format_for_retriever) | retriever | format_document}
            | RunnableLambda(format_for_prompt_template) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return conversation_chain


if __name__ == "__main__":
    # session id 配置
    session_config = {
        "configurable": {
            "session_id": "user_001",
        }
    }
    res = RagService().chain.invoke({"input": "简述蒙德的建成历史"}, session_config)
    print(res)