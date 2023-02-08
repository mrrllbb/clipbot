from socket import *
import time
import traceback
from threading import Thread


class RegisterServer():
    def __init__(self, socket_port, namespace, client_list=[]):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        # 设置套接字
        self.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.socket_server_on = False
        self.namespace = namespace
        self.client_list = client_list
        if len(self.client_list) == 0:
            self.client_list.append(self.get_host())
        self.server_thread = Thread(target=self.run)
        # 选择一个接收地址
        try:
            self.socket.bind(('0.0.0.0', socket_port))
            self.socket_server_on = True
            print(f"socket服务器启动，端口{socket_port}")
        except OSError:
            assert self.socket_server_on, f"{socket_port}端口已被占用，请更换端口后重试"

    def run(self):
        while True:
            if not self.socket_server_on:
                print("socket服务器已关闭")
                break
            try:
                msg, addr = self.socket.recvfrom(1024)
                msg = msg.decode('utf-8')
                ip, port = addr
                op, current_namespace = msg.strip().split(':')
                print(f'接收消息==客户端地址:{addr},namespace:{current_namespace},op:{op}')
                if current_namespace != self.namespace:
                    continue
                if op == "connect":
                    if ip not in self.client_list:
                        self.client_list.append(ip)
                        print(f"客户端{ip}连接成功")
                elif op == "disconnect":
                    if ip in self.client_list:
                        self.client_list.remove(ip)
                        print(f"客户端{ip}已离线")
                self.socket.sendto("我是注册服务端,我的时间是{}".format(time.time()).encode('utf-8'), addr)
            except:
                print("接收消息异常:{}".format(traceback.format_exc()))

    def start(self):
        self.server_thread.start()
        print("socket服务器已开始监听")

    def close(self):
        # self.send_addr_to_client()
        self.socket.close()
        self.socket_server_on = False

    def send_addr_to_client(self):
        temp_server_addr = self.client_list.pop()
        client_msg = ";".join(self.client_list)
        assert self.socket_server_on, "socket服务器未开启"
        self.socket.sendto(f"send_addr_to_client:{client_msg}".encode('utf-8'), temp_server_addr)

    def get_client_list(self):
        return self.client_list

    @staticmethod
    def get_host():
        return gethostbyname(gethostname())


if __name__=="__main__":
    rs = RegisterServer(9999, "shaoyiming")
    rs.start()
    print("test")
    # rs.close()