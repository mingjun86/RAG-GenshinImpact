import os
import json
from typing import Sequence, List, Dict, Any
from datetime import datetime
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage, HumanMessage, AIMessage

# 对话存储目录
CONVERSATIONS_DIR = "saved_conversations"


def get_conversation_list(use_cache=True) -> List[Dict[str, Any]]:
    """获取所有保存的对话列表（只返回有用户消息的对话）"""
    if not os.path.exists(CONVERSATIONS_DIR):
        return []

    conversations = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                messages = data.get("messages", [])
                # 只保留有用户消息的对话
                has_user = any(msg.get("role") == "user" for msg in messages)

                if has_user:
                    conversations.append({
                        "id": filename.replace(".json", ""),
                        "title": data.get("title", "未命名对话"),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": len(data.get("messages", []))
                    })
            except:
                pass

    # 按更新时间倒序排列（最新的在前）
    conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return conversations


def save_conversation(conversation_id: str, title: str, messages: List[Dict], update_timestamp=True):
    """保存对话到文件

    Args:
        conversation_id: 对话ID
        title: 对话标题
        messages: 消息列表
        update_timestamp: 是否更新时间戳（只有内容变化时才更新）
    """
    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")

    # 读取旧数据（如果存在）
    old_data = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

    data = {
        "id": conversation_id,
        "title": title,
        "messages": messages,
        "created_at": old_data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        # 只有内容变化或强制更新时才更新 updated_at
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if update_timestamp else old_data.get("updated_at",
                                                                                                         datetime.now().strftime(
                                                                                                             "%Y-%m-%d %H:%M:%S"))
    }

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


def has_user_message(conversation_id: str) -> bool:
    """检查对话是否有用户消息（是否为空对话）"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if not os.path.exists(filepath):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        messages = data.get("messages", [])
        return any(msg.get("role") == "user" for msg in messages)
    except:
        return False