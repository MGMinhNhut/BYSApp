import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from backend.logic import LoginUI, CreateAccUI, resource_path 

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    app.setWindowIcon(QIcon(resource_path("images/logo.ico")))
    
    login_window = LoginUI()
    create_acc_window = CreateAccUI()

    widget = QtWidgets.QStackedWidget()
    widget.addWidget(login_window)     
    widget.addWidget(create_acc_window) 
    
    import backend.logic as logic
    logic.widget = widget 

    widget.resize(600, 800)
    widget.setWindowTitle("BYS-App")
    widget.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()