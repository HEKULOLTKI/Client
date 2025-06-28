from PyQt5.QtCore import QObject, pyqtSignal
import requests
import threading
from src.core import config
import json
import re

class OpenAIChat(QObject):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_id = "8dfc6b34541711f0a2b90242ac130006"
        self.url = f'http://10.10.20.121/api/v1/chats_openai/{self.chat_id}/chat/completions'
        self.api_key = 'ragflow-I0YTgzNzdjNTQxNzExZjA4YzY0MDI0Mm'
        self.lock = threading.Lock()

    def chat_async(self, messages, max_tokens=204800):
        def _chat_thread():
            try:
                with self.lock:
                    data = {
                        "model": "qwen2.5:32b",
                        "messages": messages,
                        "max_tokens": max_tokens
                    }
                    headers = {
                        'Authorization': f'Bearer {self.api_key}',
                        'content-Type': 'application/json',
                        'accept': 'application/json'
                    }
                    resq = requests.post(self.url, headers=headers, json=data, timeout=60)
                    resq.raise_for_status()
                    text = resq.text.strip()
                    if not text:
                        self.error_occurred.emit("接口无响应或返回内容为空。")
                        return
                    if text.startswith("data:"):
                        text = text[5:].strip()
                    matches = re.findall(r'"content"\s*:\s*"([^"]+)"', text)
                    if matches:
                        content = "".join(matches)
                        # 过滤所有以##开头到空格、换行或结尾的特殊字符
                        content = re.sub(r'##[^\s\n]*', '', content)
                        content = content.replace('\\n', '\n')
                        self.response_received.emit(content)
                        return
                    if "code" in text and "109" in text:
                        self.error_occurred.emit("API密钥无效，请检查API Key设置。")
                        return
                    self.error_occurred.emit(f"无法解析AI回复内容：{text[:200]}")
            except Exception as e:
                self.error_occurred.emit(str(e))
        thread = threading.Thread(target=_chat_thread)
        thread.daemon = True
        thread.start()

    def chat(self, messages, max_tokens=2048):
        try:
            data = {
                "mode": "qwen2.5:32b",
                "model": "qwen2.5:32b",
                "messages": messages,
                "max_tokens": max_tokens
            }
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'content-Type': 'application/json',
                'accept': 'application/json'
            }
            resq = requests.post(self.url, headers=headers, json=data, timeout=60)
            resq.raise_for_status()
            text = resq.text.strip()
            if not text:
                return "接口无响应或返回内容为空。"
            if text.startswith("data:"):
                text = text[5:].strip()
            matches = re.findall(r'"content"\s*:\s*"([^"]+)"', text)
            if matches:
                content = "".join(matches)
                content = re.sub(r'##[^\s\n]*', '', content)
                content = content.replace('\\n', '\n')
                return content
            if "code" in text and "109" in text:
                return "API密钥无效，请检查API Key设置。"
            return f"无法解析AI回复内容：{text[:200]}"
        except Exception as e:
            return f"Error: {str(e)}"