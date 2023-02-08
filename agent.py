# UDP广播案例-发送端
import json
import os
import pkgutil
import sys
from socket import *
import time
import threading
from registerSever import RegisterServer
import traceback
from flask import Flask, Blueprint
import requests
import api
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QMimeData, QUrl
from utils.signal import clipboard_update_signal



class Agent():
    def __init__(self, port, socket_port, namespace, blueprint_path='api/'):
        self.port = port
        self.socket_port = socket_port
        self.namespace = namespace
        self.blueprint_path = blueprint_path
        self.app = Flask(__name__)
        self.socket_client = socket(AF_INET, SOCK_DGRAM)
        self.socket_client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.register_server = None
        self.server_address = "127.0.0.1"
        self.found = False
        self.blueprint_dict = {}
        self.qt_app = QApplication([])
        self.clipboard = self.qt_app.clipboard()
        self.clipboard.dataChanged.connect(self.get_clipboard)
        self.ip = RegisterServer.get_host()
        self.remote_flag = False

    def switch_remote_flag(self, flag=None):
        if flag is None:
            self.remote_flag = not self.remote_flag
        else:
            self.remote_flag = flag


    def discover(self, ip):
        """向指定ip发送socket发现注册服务器"""
        # 设定目标地址
        # print(ip)
        try:
            dest = (ip, self.socket_port)  # 192.168.31是我的网段,255代表任意IP
            data = f'connect:{self.namespace}'
            self.socket_client.sendto(data.encode('utf-8'), dest)  # 发送广播
            self.socket_client.settimeout(0.1)  # 设置等待超时时间为0.1s
            msg, addr = self.socket_client.recvfrom(1024)  # recvfrom为阻塞方法
            self.server_address = addr[0]
            self.app.extensions['server_address'] = self.server_address
            self.found = True
            print('连接成功==服务端地址:{},响应内容:{}'.format(addr, msg.decode('utf-8')))

        except:
            pass

    def scan(self):
        """扫描局域网，发现注册服务器"""
        try:
            print("扫描局域网")
            for ip1 in range(255):
                if self.found:
                    break
                for ip2 in range(255):
                    if self.found:
                        print("发现服务器")
                        break
                    t = threading.Thread(target=self.discover, args=(f"192.168.{ip1}.{ip2}",))
                    t.start()
        except:
            print(f"扫描异常:{traceback.format_exc()}")

    def start(self):
        self.connect()
        self.start_flask_app()
        self.qt_app.exec_()

    def connect(self):
        """连接socket注册服务器"""
        self.scan()
        if not self.found:
            self.register_server = RegisterServer(self.socket_port, self.namespace)
            self.register_server.start()
            self.app.extensions['register_server'] = self.register_server

    def disconnect(self):
        """断连socket注册服务器"""
        try:
            dest = (self.server_address, self.port)  # 192.168.31是我的网段,255代表任意IP
            data = f'disconnect:{self.namespace}'
            self.socket_client.sendto(data.encode('utf-8'), dest)  # 发送广播
            self.socket_client.settimeout(1)  # 设置等待超时时间为1s
            msg, addr = self.socket_client.recvfrom(1024)  # recvfrom为阻塞方法
            print('连接成功==服务端地址:{},响应内容:{}'.format(addr, msg.decode('utf-8')))
        except:
            pass

    def start_flask_app(self):
        """启动flask"""
        self.add_blueprint()
        kwargs = {'host': '0.0.0.0', 'port': self.port, 'threaded': True}

        #   running flask thread
        threading.Thread(target=self.app.run, daemon=True, kwargs=kwargs).start()

    def add_blueprint(self):
        """将flask蓝图加载到flask app"""
        pkg_list = pkgutil.walk_packages(api.__path__, api.__name__ + ".")
        for _, module_name, ispkg in pkg_list:
            __import__(module_name)
            print(module_name)
            module = sys.modules[module_name]
            module_attrs = dir(module)
            for name in module_attrs:
                var_obj = getattr(module, name)
                if isinstance(var_obj, Blueprint):
                    if self.blueprint_dict.get(name) is None:
                        self.blueprint_dict[name] = var_obj
                        self.app.register_blueprint(var_obj)
                        print(f" * 注入 {Blueprint.__name__} 模块 {var_obj.__str__()} 成功")

    def get_client_list(self):
        """获得client_list"""
        if self.register_server:
            return self.register_server.get_client_list()
        else:
            return self.get_client_list_from_server()

    def get_client_list_from_server(self):
        """从register_server获得client_list"""
        url = f"{self.server_address}:{self.port}/clipboard/get_agent"
        response = requests.request("GET", url)
        res_data = response.content.get('data')
        return res_data

    def get_clipboard(self):
        if not self.remote_flag:
            data = self.clipboard.mimeData()
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
            self.send_clipboard(file_list, text)

    def send_clipboard(self, file_list, text):
        """同步agent的剪切板"""
        for tip in self.get_client_list():
            if tip != self.ip:
                url = f"http://{tip}:{self.port}/clipboard/update_clipboard"
                payload = json.dumps({"text": text, "file_list": file_list})
                headers = {'Content-Type': 'application/json'}
                response = requests.request("POST", url, headers=headers, data=payload, timeout=1)





if __name__ == "__main__":
    agent = Agent(19999, 9999, "shaoyiming")

    @clipboard_update_signal.connect
    def update_clipboard(sender, *args, **kwargs):
        agent.switch_remote_flag(True)
        file_list = kwargs["file_list"]
        text = kwargs["text"]
        if text:
            agent.clipboard.setText(text)
        if file_list:
            print(file_list)
    agent.start()