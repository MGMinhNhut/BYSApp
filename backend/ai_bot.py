import sys
import re
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
from openai import OpenAI
from dotenv import load_dotenv

def resource_path(relative_path):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

load_dotenv(resource_path(".env"))

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))

class AIWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def run(self):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=self.messages,
                stream=True,
                max_tokens=400
            )
            
            full_reply = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_reply += content
                    self.chunk_received.emit(content)
            
            self.finished.emit(full_reply)
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate_limit" in error_str:
                friendly_msg = "Byson đang xử lý hơi nhiều việc. Byser đợi một chút rồi nhắn lại nhé!"
                self.error_occurred.emit(friendly_msg)
            else:
                self.error_occurred.emit(f"Sự cố kết nối: {str(e)}")

class BYSONApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(BYSONApp, self).__init__()
        uic.loadUi(resource_path('frontend/ai_chat.ui'), self)
        
        self.messages = [{"role": "system", "content": """You are my BYS App Assistant, a To-do list app to help users make their own schedule. You call yourself 'BYSON' and call me 'Byser'(người dùng BYS). You can tease me sometime for a friendly atmosphere but when it comes to work, seriousness is the key. You must keep the advice short(under 50 words) when the solutions are short and easy to understand. IF the solutions required a long and essential for user, don't hesitate to explain it clearly.You can only show your knowledge in building any types of schedule, recommend activities for a day or for a week, or help users building their schedule for a specific purpose. You should also show your knowledge in weather and other related topics. Any other topics besides to-do list and weather you must kindly reject users. Since you were programmed for a Vietnamese app, you must use all terms as Vietnamese as possible. You must know that Vietnam's timezone is UTC+7. Use this to access weather and time easier. Always respond with Vietnamese."""}]
        
        self.send_btn.clicked.connect(self.handle_send)
        self.user_input.returnPressed.connect(self.handle_send)
        
        self.user_input.setMaxLength(300)
        
        self.chat_history.setStyleSheet("font-size: 20px; padding: 10px; background-color: #f9f9f9;")

    def trim_chat_history(self):
        MAX_MESSAGES = 7 
        if len(self.messages) > MAX_MESSAGES:
            system_prompt = self.messages[0]
            recent_messages = self.messages[-(MAX_MESSAGES - 1):]
            self.messages = [system_prompt] + recent_messages

    def handle_send(self):
        text = self.user_input.text().strip()
        if not text: return

        self.append_user_message(text)
        self.user_input.clear()
        self.send_btn.setEnabled(False)

        self.messages.append({"role": "user", "content": text})
        
        self.trim_chat_history()

        self.chat_history.append(f"<b style='color: red;'>BYSON:</b> ")
        self.cursor = self.chat_history.textCursor()
        self.cursor.movePosition(QTextCursor.End)

        self.worker = AIWorker(self.messages)
        self.worker.chunk_received.connect(self.handle_chunk)
        self.worker.finished.connect(self.handle_finished)
        self.worker.error_occurred.connect(self.handle_error)
        
        self.worker.finished.connect(self.worker.deleteLater) 
        self.worker.error_occurred.connect(lambda: self.worker.deleteLater())
        
        self.worker.start()

    def append_user_message(self, text):
        self.chat_history.append(f"<b style='color: blue;'>Bạn:</b> {text}<br>")

    def handle_chunk(self, content):
        self.cursor.insertText(content)
        self.chat_history.ensureCursorVisible()

    def handle_finished(self, full_reply):
        self.send_btn.setEnabled(True)
        if full_reply:
            self.messages.append({"role": "assistant", "content": full_reply})
            self.chat_history.append("") 

    def handle_error(self, error_msg):
        self.send_btn.setEnabled(True)
        self.chat_history.append(f"<i style='color: gray;'>Lỗi: {error_msg}</i>")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = BYSONApp()
    window.show()
    sys.exit(app.exec_())