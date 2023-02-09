import os
from blinker import Namespace
from PyQt5.QtWidgets import QApplication
from threading import Thread

signal = Namespace().signal('clipboard')

qt_app = QApplication([])
clipboard = qt_app.clipboard()
init_data = clipboard.mimeData()
def listen_clipboard():
    init_text = init_data.text()
    init_file_list = init_data.urls()
    while True:
        data = clipboard.mimeData()
        if data.text() != init_text or data.urls() != init_file_list:
            init_text = data.text()
            init_file_list = data.urls()
            signal.send()

@signal.connect
def get_clipboard(sender):
    data = clipboard.mimeData()
    print(data.formats())
    file_list = []
    text = ""
    if data.hasFormat('text/uri-list'):
        for path in data.urls():
            # 打印复制的路径
            temp_path = path.path()[1:]
            print(temp_path)
            if os.path.isfile(temp_path):
                file_list.append(temp_path)
    # 如果是纯文本类型，打印文本的值
    if data.hasFormat('text/plain'):
        text = data.text()
    print(text)
# clipboard.dataChanged.connect(get_clipboard)
Thread(target=listen_clipboard).start()
qt_app.exec_()