import os,json
from typing import Sequence
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory


def get_history(session_id):
    return FileChatMessageHistory(session_id, "chat_history")

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self,session_id,storage_path):
         self.session_id = session_id
         self.storage_path = storage_path

         self.file_path = os.path.join(self.storage_path,self.session_id)

         os.makedirs(os.path.dirname(self.file_path),exist_ok=True)

    def add_messages(self,messages:Sequence[BaseMessage])->None:
     #Sequence序列类似list
        all_messages = list(self.messages)
        all_messages.extend(messages)


        new_messages = [ message_to_dict(message) for message in all_messages]
        #将数据写入文件
        with open(self.file_path,'w',encoding='utf-8') as f:
         json.dump(new_messages,f)

    @property   #property装饰器将messages方法变成成员变量
    def messages(self)->list[BaseMessage]:
        #当前文件list[字典]
        try:
            with open(self.file_path,'r',encoding='utf-8') as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self)->None:
        with open(self.file_path,"w",encoding="utf-8") as f:
            json.dump([],f)