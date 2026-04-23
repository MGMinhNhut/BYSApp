from datetime import datetime
import requests
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QLineEdit, QScrollArea
from PyQt5.uic import loadUi
import sys
import pyrebase
import os
import json
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag
from dotenv import load_dotenv
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QCheckBox
from backend.ai_bot import BYSONApp
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt

def resource_path(relative_path):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

load_dotenv(resource_path(".env"))

firebaseConfig={
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
    'projectId': "bysappauthen",
    'storageBucket': "bysappauthen.firebasestorage.app",
    'messagingSenderId': "160093051770",
    'appId': "1:160093051770:web:6a84e86e1763cdbb38d4c3",
    'measurementId': "G-E2MZKNR7V2"
}

firebase=pyrebase.initialize_app(firebaseConfig)
auth=firebase.auth()
db = firebase.database()

class LoginLoader(QThread):
    finished_loading = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, email, password):
        super().__init__()
        self.email = email
        self.password = password

    def run(self):
        try: 
            login = auth.sign_in_with_email_and_password(self.email, self.password)
            user_info = auth.get_account_info(login['idToken'])
            is_verified = user_info['users'][0]['emailVerified']

            if is_verified:
                self.finished_loading.emit(login)
            else:
                self.error_signal.emit("Vui lòng xác thực email trước khi đăng nhập!")
        except Exception:
            self.error_signal.emit("Email hoặc mật khẩu không đúng")

class LoginUI(QDialog):
    def __init__(self):
        super(LoginUI, self).__init__()

        loadUi(resource_path("frontend/login.ui"), self)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.loading_timer = QtCore.QTimer()
        self.loading_timer.timeout.connect(self.animated_dots)
        self.dot_count = 0

        self.Login_button.clicked.connect(self.Login_function)
        self.Email_input.returnPressed.connect(self.Login_function)
        self.Password_input.returnPressed.connect(self.Login_function)
        self.Password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.Create_acc_button.clicked.connect(self.Creat_acc_function)
        self.Forgot_pass_button.clicked.connect(self.Forgot_pass_function)

    def animated_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        self.Login_button.setText("." * self.dot_count)

    def start_loading_effect(self):
        self.Login_button.setEnabled(False)
        self.loading_timer.start(200)
    
    def stop_loading_effect(self):
        self.loading_timer.stop()
        self.Login_button.setEnabled(True)
        self.Login_button.setText("Login")

    def Forgot_pass_function(self):
        email, okay = QtWidgets.QInputDialog.getText(self, 'Quên mật khẩu', 'Nhập email của bạn:')

        if okay and email:
            try:
                auth.send_password_reset_email(email)
                QMessageBox.information(self, "Thành công", "Vui lòng kiểm tra email để được cấp lại mật khẩu(Kiểm tra cả thư mục thư rác và spam)")
                self.error_label.setText("")
            except Exception as e:
                self.error_label.setText("Không thể gửi email reset. Vui lòng kiểm tra lại email!")
        elif okay and not email:
            self.error_label.setText("Vui lòng nhập email rồi ấn OK!")

    def reset_field(self):
        self.Email_input.clear()
        self.Password_input.clear()
        self.error_label.setText("")
        self.stop_loading_effect()

    def Login_function(self):
        email = self.Email_input.text()
        password = self.Password_input.text()

        if not email or not password:
            self.error_label.setText("Vui lòng nhập đầy đủ thông tin")
            return
        
        self.start_loading_effect()
        self.error_label.setText("")

        self.login_loader = LoginLoader(email, password)
        self.login_loader.finished_loading.connect(self.on_login_success)
        self.login_loader.error_signal.connect(self.on_login_error)
        self.login_loader.start()
    
    def on_login_success(self, login_data):
        self.stop_loading_effect()
        self.after_login = WeeklyTodoUI(login_data['email'], login_data['idToken'])
        widget.addWidget(self.after_login)
        widget.setCurrentWidget(self.after_login)
        widget.setWindowTitle("BYS-Main Window")
        widget.showMaximized()
        self.login_loader.deleteLater()

    def on_login_error(self, message):
        self.stop_loading_effect()
        self.error_label.setText(message)
        

    def Creat_acc_function(self):
        sign_up_screen = widget.widget(1)
        sign_up_screen.reset_fields()

        widget.setCurrentIndex(1)
        widget.setWindowTitle("BYS-Sign up")
        self.reset_field()

class CreateAccUI(QDialog):
    def __init__(self):
        super(CreateAccUI, self).__init__()

        loadUi(resource_path("frontend/create_acc.ui"), self)

        self.SignUp_button.clicked.connect(self.signup_function)
        self.Password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.Confirm_Password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.Back_button.clicked.connect(self.Back_to_login)
        self.error_label.setText("")

    def signup_function(self):
        email = self.Email_input.text()
        password = self.Password_input.text()
        confirm_password = self.Confirm_Password_input.text()
        
        if not email or not password or not confirm_password:
            self.error_label.setText("Vui lòng điền đầy đủ thông tin!")
            return
        if len(password) < 6:
            self.error_label.setText("Mật khẩu quá yếu. Tối thiểu 6 kí tự!")
            return
        if password != confirm_password:
            self.error_label.setText("Mật khẩu xác nhận không khớp!")
            return
        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            QMessageBox.information(self, "Thông báo!", "Tạo tài khoản thành công! Vui lòng kiếm tra email để xác thực tài khoản!(Kiểm tra cả thư mục thư rác và spam)")
            self.error_label.setText("")
            self.Back_to_login()
        except Exception as e:
            self.error_label.setText("Email đã tồn tại hoặc không hợp lệ!")
            
    def Back_to_login(self):
        widget.setCurrentIndex(0)
        widget.setWindowTitle("BYS-Login")
        login_screen = widget.widget(0)
        login_screen.reset_field()
    
    def reset_fields(self):
        self.Email_input.clear()
        self.Password_input.clear()
        self.Confirm_Password_input.clear()
        self.error_label.setText("")

class WeatherLoader(QThread):
    completed_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, city):
        super().__init__()
        self.city = city

    def run(self):
        try: 
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.city}&count=1&language=vi"
            geo_response = requests.get(geo_url).json()

            if "results" not in geo_response:
                self.error_signal.emit("Lỗi! Không tìm thấy thành phố!")
                return

            lat = geo_response["results"][0]["latitude"]
            lon = geo_response["results"][0]["longitude"]

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max&timezone=auto"
            weather_response = requests.get(weather_url).json()

            self.completed_signal.emit(weather_response['daily'])
        except Exception as e:
            self.error_signal.emit(str(e))

class WeatherApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(WeatherApp, self).__init__()
        loadUi(resource_path("frontend/weather.ui"), self)
        
        self.searchBtn.clicked.connect(self.get_weather)
        self.cityInput.returnPressed.connect(self.get_weather)
        
        self.bg_image_path = None 

    def get_weather(self):
        city = self.cityInput.text().strip()
        if not city: 
            return

        self.searchBtn.setText("Đang tải...")
        self.searchBtn.setEnabled(False)

        self.worker = WeatherLoader(city)
        self.worker.completed_signal.connect(self.on_weather_success)
        self.worker.error_signal.connect(self.on_weather_error)
        self.worker.start()
    
    def on_weather_success(self, daily_data):
        self.update_ui(daily_data) 
        self.reset_search_btn()
        
        try:
            today_weather_code = daily_data['weathercode'][0]
            self.bg_image_path = self.get_weather_image_path(today_weather_code)
        except (KeyError, IndexError):
            self.bg_image_path = None
            
        self.update() 
    
    def on_weather_error(self, error_msg):
        QtWidgets.QMessageBox.warning(self, "Lỗi", error_msg)
        self.reset_search_btn()
        
        self.clear_layout(self.forecastContainer)

        self.bg_image_path = None
        self.update()
    
    def reset_search_btn(self):
        self.searchBtn.setText("Tìm kiếm")
        self.searchBtn.setEnabled(True)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def get_weather_desc(self, code):
        """Hàm dịch mã thời tiết của API sang tiếng Việt"""
        wmo_codes = {
            0: "Trời quang", 1: "Ít mây", 2: "Mây rải rác", 3: "Nhiều mây",
            45: "Sương mù", 48: "Sương mù lạnh",
            51: "Mưa phùn nhẹ", 53: "Mưa phùn vừa", 55: "Mưa phùn dày",
            61: "Mưa nhỏ", 63: "Mưa vừa", 65: "Mưa to",
            71: "Tuyết rơi nhẹ", 73: "Tuyết rơi", 75: "Tuyết rơi dày",
            95: "Mưa dông", 96: "Dông kèm mưa đá", 99: "Dông kèm mưa đá to"
        }
        return wmo_codes.get(code, "Không xác định")

    def get_weather_image_path(self, code):
        """Hàm phân loại mã thời tiết và trả về đường dẫn ảnh tương ứng"""
        if code in [0, 1, 2]: return resource_path("images/clear.jpg")         
        elif code in [3]: return resource_path("images/cloudy.jpg")        
        elif code in [45, 48]: return resource_path("images/fog.jpg")     
        elif code in [51, 53, 55, 61, 63, 65]: return resource_path("images/rain.jpg") 
        elif code in [71, 73, 75]: return resource_path("images/snow.jpg")   
        elif code in [95, 96, 99]: return resource_path("images/storm.jpg")     
        return None

    def paintEvent(self, event):
        """Ghi đè hàm paintEvent để vẽ ảnh nền mờ xuống dưới cùng"""
        super().paintEvent(event)

        if self.bg_image_path:
            painter = QtGui.QPainter(self)
            pixmap = QtGui.QPixmap(self.bg_image_path)
            
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
                
                x = (self.width() - scaled_pixmap.width()) // 2
                y = (self.height() - scaled_pixmap.height()) // 2
                
                painter.setOpacity(0.8) 
                
                painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()

    def update_ui(self, daily_data):
        self.clear_layout(self.forecastContainer)
        
        time_list = daily_data['time']
        codes = daily_data['weathercode']
        temps = daily_data['temperature_2m_max']
        humids = daily_data['relative_humidity_2m_mean']
        winds_kmh = daily_data['wind_speed_10m_max']

        for i in range(len(time_list)):
            dt = datetime.strptime(time_list[i], "%Y-%m-%d")
            
            days_vn = {"Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4", 
                       "Thursday": "Thứ 5", "Friday": "Thứ 6", "Saturday": "Thứ 7", "Sunday": "Chủ Nhật"}
            day_vn = days_vn.get(dt.strftime('%A')) + dt.strftime(', %d/%m')

            desc = self.get_weather_desc(codes[i])
            temp = temps[i]
            humidity = humids[i]
            wind_ms = round(winds_kmh[i] / 3.6, 2)


            row_frame = QFrame()
            row_frame.setFrameShape(QFrame.StyledPanel)
            row_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: 1px solid #E2E8F0;
                }
                QLabel {
                    font-size: 16px;
                    color: #2D3748;
                    border: none;
                    font-weight: 500;
                }
            """)
            h_layout = QHBoxLayout()

            lbl_date = QLabel(f"<b>{day_vn}</b>")
            lbl_desc = QLabel(desc)
            lbl_temp = QLabel(f"🌡️ {temp} °C")
            lbl_humid = QLabel(f"💧 {humidity} %")
            lbl_wind = QLabel(f"💨 {wind_ms} m/s")

            for lbl in [lbl_date, lbl_desc, lbl_temp, lbl_humid, lbl_wind]:
                lbl.setMinimumWidth(120)
                h_layout.addWidget(lbl)

            row_frame.setLayout(h_layout)
            self.forecastContainer.addWidget(row_frame)
            
        self.forecastContainer.addStretch()

class EditDialog(QDialog):
    def __init__(self, current_time, current_task, parent=None):
        super(EditDialog, self).__init__(parent)
        
        loadUi(resource_path("frontend/fix_todo.ui"), self)
        self.setWindowTitle("Chỉnh sửa công việc")
        

        self.lineEdit.setText(current_time)
        self.lineEdit_2.setText(current_task)
        
        self.pushButton.clicked.connect(self.accept)
        regex = QRegExp(r"^[0-9:\s\-]+$") 
        validator = QRegExpValidator(regex)
        self.lineEdit.setValidator(validator)

    def get_values(self):
        return self.lineEdit.text().strip(), self.lineEdit_2.text().strip()

class TaskCard(QFrame):
    def __init__(self, day, time, task, completed, edit_callback, delete_callback, complete_callback):
        super().__init__()
        self.day = day
        self.time_str = time
        self.task_str = task
        self.completed = completed

        bg_color = "#f4f6f8" if completed else "white"
        border_color = "#1A73E8" if completed else "#e1e8ed"
        
        self.setStyleSheet(f"""
            QFrame {{ background-color: {bg_color}; border-radius: 8px; border: 1px solid {border_color}; }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        self.setMinimumHeight(60) 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(completed)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator { width: 22px; height: 22px; border-radius: 11px; border: 1.5px solid #b2bec3; background-color: white; }
            QCheckBox::indicator:hover { border: 1.5px solid #1A73E8; }
            QCheckBox::indicator:checked { 
                background-color: #1A73E8; border: 1.5px solid #1A73E8; 
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNCIgaGVpZ2h0PSIxNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiLz48L3N2Zz4=);
            }
        """)
        from PyQt5.QtCore import Qt
        self.checkbox.stateChanged.connect(complete_callback)

        time_color = "#a0aab5" if completed else "#e67e22"
        task_color = "#a0aab5" if completed else "#2d3436"
        task_style = "text-decoration: line-through;" if completed else "font-weight: bold;"
        
        html_text = f"""
        <span style='color: {time_color}; font-weight: bold; font-size: 15px;'>[{time}] </span>
        <span style='color: {task_color}; font-size: 16px; {task_style}'>{task}</span>
        """
        
        self.lbl_task = QLabel()
        self.lbl_task.setTextFormat(Qt.RichText)
        self.lbl_task.setText(html_text)
        self.lbl_task.setWordWrap(True)
        self.lbl_task.setOpenExternalLinks(False)

        btn_edit = QPushButton("Sửa")
        btn_edit.setFixedWidth(55) 
        btn_edit.setStyleSheet("background-color: #0078D4; color: white; border-radius: 4px; font-size: 13px; padding: 6px;")
        btn_edit.clicked.connect(edit_callback)

        btn_del = QPushButton("Xóa")
        btn_del.setFixedWidth(55) 
        btn_del.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 4px; font-size: 13px; padding: 6px;")
        btn_del.clicked.connect(delete_callback)

        layout.addWidget(self.checkbox, 0, Qt.AlignTop)
        layout.addWidget(self.lbl_task, 1) 
        layout.addWidget(btn_edit, 0, Qt.AlignTop)
        layout.addWidget(btn_del, 0, Qt.AlignTop)

    def mousePressEvent(self, event):
        from PyQt5.QtCore import Qt
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        from PyQt5.QtCore import Qt, QMimeData, QByteArray
        from PyQt5.QtGui import QDrag
        from PyQt5.QtWidgets import QApplication
        import json
        
        if not (event.buttons() & Qt.LeftButton): return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance(): return
        
        drag = QDrag(self)
        mime_data = QMimeData()
        
        task_info = {'day': self.day, 'time': self.time_str, 'task': self.task_str, 'completed': self.completed}
        json_string = json.dumps(task_info)
        
        mime_data.setData("application/json", QByteArray(json_string.encode('utf-8')))
        
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.exec_(Qt.MoveAction)
class DayDropFrame(QFrame):
    """Khung Kanban của từng ngày"""
    def __init__(self, day_name, drop_callback):
        super().__init__()
        self.day_name = day_name
        self.drop_callback = drop_callback
        self.setAcceptDrops(True)
        self.setFixedWidth(450) 
        self.setStyleSheet("DayDropFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #e1e8ed; }")
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/json"):
            self.setStyleSheet("DayDropFrame { background-color: #f1f8ff; border-radius: 12px; border: 2px dashed #0078D4; }")
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/json"):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("DayDropFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #e1e8ed; }")

    def dropEvent(self, event):
        self.setStyleSheet("DayDropFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #e1e8ed; }")
        if event.mimeData().hasFormat("application/json"):
            try:
                import json
                byte_data = event.mimeData().data("application/json")
                json_string = bytes(byte_data).decode('utf-8')
                task_info = json.loads(json_string)
                
                self.drop_callback(self.day_name, task_info['day'], task_info)
                event.acceptProposedAction()
            except Exception as e:
                import traceback
                print("Lỗi kéo thả:", e)
                print(traceback.format_exc())


class WeeklyTodoUI(QMainWindow):
    def __init__(self, email, idToken):
        super(WeeklyTodoUI, self).__init__()
        
        loadUi(resource_path("frontend/todo_main.ui"), self)
        
        self.email = email
        self.idToken = idToken
        self.safe_email = email.replace(".", "_").replace("@", "_").replace("#", "_")
        self.data = {day: [] for day in ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]}
        self.day_layouts = {}
        
        self.user_label.setText(f"Tài khoản: {self.email}")
        self.logout_btn.clicked.connect(self.log_out_function)
        self.logout_btn.setFixedSize(120, 35)
        
        self.weather_app = WeatherApp()
        self.weather_tab_container.layout().addWidget(self.weather_app)
        
        self.init_kanban_board()
        
        self.load_data_from_firebase()

        self.ai_window = None 

        self.chat_bubble = QPushButton("", self)
        self.chat_bubble.setFixedSize(70, 70)
        self.chat_bubble.setCursor(Qt.PointingHandCursor)

        chatbot_img_path = resource_path("images/chatbot.png").replace("\\", "/")

        self.chat_bubble.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; 
                border-image: url("{chatbot_img_path}"); 
                border-radius: 35px; 
                border: none; 
            }}
            
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 30); 
            }}
        """)
        self.chat_bubble.clicked.connect(self.open_ai_chat)

    def init_kanban_board(self):
        for day in self.data.keys():
            col_frame = DayDropFrame(day, self.handle_task_drop)
            vbox = QVBoxLayout(col_frame)
            
            lbl_day = QLabel(day.upper())
            lbl_day.setObjectName("col_header")
            lbl_day.setAlignment(QtCore.Qt.AlignCenter)
            vbox.addWidget(lbl_day) 
            
            input_layout = QVBoxLayout()
            t_in = QLineEdit()
            t_in.setPlaceholderText("08:00 - 09:00")
            t_in.setProperty("class", "kanban_input")
            t_in.setValidator(QRegExpValidator(QRegExp(r"^[0-9:\s\-]+$")))
            
            e_in = QLineEdit()
            e_in.setPlaceholderText("Nhập việc...")
            e_in.setProperty("class", "kanban_input")
            
            btn = QPushButton("+ Thêm")
            btn.setObjectName("btn_add_task")
            
            input_layout.addWidget(t_in)
            input_layout.addWidget(e_in)
            input_layout.addWidget(btn)
            
            btn.clicked.connect(lambda _, d=day, t=t_in, e=e_in: self.add_task(d, t, e))
            
            vbox.addLayout(input_layout)

            tasks_container = QWidget()
            tasks_layout = QVBoxLayout(tasks_container)
            tasks_layout.setContentsMargins(0,0,0,0)
            tasks_layout.setAlignment(QtCore.Qt.AlignTop)
            self.day_layouts[day] = tasks_layout
            
            scroll_tasks = QScrollArea()
            scroll_tasks.setWidgetResizable(True)
            scroll_tasks.setWidget(tasks_container)
            
            vbox.addWidget(scroll_tasks)
            
            self.kanban_layout.addWidget(col_frame)
            
        self.kanban_layout.addStretch()

    def load_data_from_firebase(self):
        try:
            db_data = db.child("users").child(self.safe_email).child("todos").get(self.idToken).val()
            if db_data:
                for day in self.data.keys():
                    if day in db_data and isinstance(db_data[day], list):
                        cleaned_list = [item for item in db_data[day] if item is not None]
                        self.data[day] = cleaned_list
                        self.refresh_ui(day)
        except Exception as e:
            print(f"Lỗi tải dữ liệu Firebase: {e}")
            QMessageBox.warning(self, "Cảnh báo", "Không thể tải dữ liệu từ máy chủ. Vui lòng kiểm tra mạng!")

    def save_to_firebase(self):
        try:
            db.child("users").child(self.safe_email).child("todos").set(self.data, self.idToken)
        except Exception as e:
            print(f"Lỗi dữ liệu: {e}")
            QMessageBox.critical(self, "Lỗi mạng", "Không thể lưu dữ liệu lên máy chủ!")

    def add_task(self, day, t_in, e_in):
        t = t_in.text().strip() or "00:00 - 00:00" 
        if "-" in t and " - " not in t:
            t = t.replace("-", " - ")
            
        e = e_in.text().strip()
        if not e: return
        new_task = {'time': t, 'task': e, 'completed': False}
        self.data[day].append(new_task)
        self.save_to_firebase()
        self.refresh_ui(day)
        t_in.clear()
        e_in.clear()
    def toggle_complete(self, day, item_dict):
        try:
            item_dict['completed'] = not item_dict.get('completed', False)
            self.save_to_firebase()
            self.refresh_ui(day)
        except Exception as e:
            print(f"Lỗi khi đánh dấu hoàn thành: {e}")
    def handle_task_drop(self, target_day, source_day, task_info):
        if target_day == source_day: return 
        
        task_to_move = None
        for t in self.data[source_day]:
            if t['time'] == task_info['time'] and t['task'] == task_info['task']:
                task_to_move = t
                break
                
        if task_to_move:
            self.data[source_day].remove(task_to_move) 
            self.data[target_day].append(task_to_move) 
            task_to_move['completed'] = False

            self.save_to_firebase()
            self.refresh_ui(source_day)
            self.refresh_ui(target_day)
    def open_ai_chat(self):
        if self.ai_window is None:
            self.ai_window = BYSONApp()
        
        self.ai_window.show()
        self.ai_window.raise_()
        self.ai_window.activateWindow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'chat_bubble'):
            self.chat_bubble.move(self.width() - 110, self.height() - 110)

    def refresh_ui(self, day):
        try:
            layout = self.day_layouts[day]
            
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
            
            self.data[day].sort(key=lambda x: str(x['time']))
            
            for entry in self.data[day]:
                card = TaskCard(
                    day,
                    entry['time'], 
                    entry['task'], 
                    entry.get('completed', False),
                    lambda _, d=day, target=entry: self.edit_task(d, target),
                    lambda _, d=day, target=entry: self.delete_task(d, target),
                    lambda _, d=day, target=entry: self.toggle_complete(d, target)
                )
                layout.addWidget(card)
        except Exception as e:
            print(f"Lỗi khi làm mới UI: {e}")
    def edit_task(self, day, item_dict):
        try:
            diag = EditDialog(item_dict['time'], item_dict['task'], self)
            if diag.exec_() == QDialog.Accepted:
                new_t, new_e = diag.get_values()
                item_dict['time'] = new_t
                item_dict['task'] = new_e
                item_dict['completed'] = False
                self.save_to_firebase()
                self.refresh_ui(day)
        except Exception as e: print(f"Lỗi khi sửa việc: {e}")

    def delete_task(self, day, item_dict):
        try:
            if item_dict in self.data[day]:
                self.data[day].remove(item_dict)
                self.save_to_firebase()
                self.refresh_ui(day)
        except Exception as e: print(f"Lỗi khi xóa việc: {e}")

    def log_out_function(self):
        widget.setCurrentIndex(0)

        login_screen = widget.widget(0)
        login_screen.reset_field()

        widget.setWindowTitle("BYS-Login")
        widget.removeWidget(self)
        self.deleteLater()