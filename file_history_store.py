import os
import json
from typing import Sequence, List, Dict, Any
from datetime import datetime
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage, HumanMessage, AIMessage

# 对话存储目录
CONVERSATIONS_DIR = "saved_conversations"


def get_conversation_list() -> List[Dict[str, Any]]:
    """获取所有保存的对话列表"""
    if not os.path.exists(CONVERSATIONS_DIR):
        return []

    conversations = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversations.append({
                        "id": filename.replace(".json", ""),
                        "title": data.get("title", "未命名对话"),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": len(data.get("messages", []))
                    })
            except:
                pass

    # 按更新时间倒序排列
    conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return conversations


def save_conversation(conversation_id: str, title: str, messages: List[Dict]):
    """保存对话到文件"""
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")

    data = {
        "id": conversation_id,
        "title": title,
        "messages": messages,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 如果文件已存在，保留创建时间
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            data["created_at"] = old_data.get("created_at", data["created_at"])

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_conversation(conversation_id: str) -> Dict[str, Any]:
    """加载指定的对话"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")

    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def delete_conversation(conversation_id: str):
    """删除指定的对话"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)


def generate_title(messages: List[Dict]) -> str:
    """根据第一条用户消息生成对话标题"""
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # 截取前30个字符作为标题
            title = content[:30] + ("..." if len(content) > 30 else "")
            return title
    return "新对话"


class FileChatMessageHistory:
    """原有的历史记录类，保持不变"""

    def __init__(self, session_id, storage_path):
        self.session_id = session_id
        self.storage_path = storage_path
        self.file_path = os.path.join(self.storage_path, self.session_id)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        all_messages = list(self.messages)
        all_messages.extend(messages)
        new_messages = [message_to_dict(message) for message in all_messages]
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(new_messages, f)

    @property
    def messages(self) -> list[BaseMessage]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)


def get_history(session_id):
    """获取历史记录（供 LangChain 使用）"""
    return FileChatMessageHistory(session_id, "chat_history")