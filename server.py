import os
import socket
import sys
import threading

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

HOST = socket.gethostname()
PORT = 9999
clients = {}
clients_lock = threading.Lock()


def broadcast(message, _sender_conn=None):
    encoded_msg = message.encode('utf-8')
    with clients_lock:
        for conn in list(clients.keys()):
            if conn != _sender_conn:
                try:
                    conn.send(encoded_msg)
                except:
                    conn.close()
                    if conn in clients:
                        del clients[conn]


def handle_client(conn, addr):
    username = "Unknown User"
    try:
        while True:
            username = conn.recv(1024).decode('utf-8')
            if not username: return

            with clients_lock:
                if username in clients.values():
                    conn.send("__username_exist__".encode('utf-8'))
                else:
                    conn.send("__success__".encode('utf-8'))
                    break

        with clients_lock:
            clients[conn] = username

        welcome_msg = f"\n[系统提示] {username} 进入了聊天室。"
        print(f"[连接] {addr} 身份确认为: {username}")
        broadcast(welcome_msg)

        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data or data == "/quit":
                break
            chat_msg = f"{username}: {data}"
            print(f"[消息] {chat_msg}")
            broadcast(chat_msg, _sender_conn=conn)

    except (ConnectionResetError, Exception) as e:
        print(f"[错误] {username} 异常: {e}")
    finally:
        with clients_lock:
            if conn in clients:
                del clients[conn]
        conn.close()
        leave_msg = f"\n[系统提示] {username} 离开了聊天室。"
        broadcast(leave_msg)
        print(f"[退出] {username} 已断开。")


def start_server_backend():
    """后台运行的服务器监听逻辑"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
    except socket.error as e:
        print(f"[失败] 无法绑定端口: {e}")
        os._exit(1)

    server.listen()
    print(f"[系统] 服务器已在 {HOST}:{PORT} 启动。输入 'help' 查看管理命令。")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()


class AdminCommand:
    def __init__(self):
        self.commands = {
            "list": self.handle_list,
            "count": self.handle_count,
            "help": self.handle_help,
            "quit": self.handle_quit,
            "say": self.handle_say  # 额外增加一个全服广播功能
        }

    def handle_list(self):
        with clients_lock:
            if not clients:
                print("当前无人在线。")
            else:
                print(f"--- 在线列表 ({len(clients)}人) ---")
                for i, name in enumerate(clients.values(), 1):
                    print(f"{i}. {name}")

    def handle_count(self):
        with clients_lock:
            print(f"当前在线人数: {len(clients)}")

    def handle_help(self):
        print("可用命令:")
        print(" - list          : 查看在线用户列表")
        print(" - count         : 查看在线人数")
        print(" - say <message> : 以系统身份向所有人发送消息")
        print(" - quit          : 关闭服务器")

    def handle_say(self, *args):
        if not args:
            print("[错误] 用法: say <消息内容>")
            return
        message = " ".join(args)
        broadcast(f"\n[服务器] {message}")
        print(f"[已发送公告] {message}")

    def handle_quit(self):
        print("正在关闭服务器...")
        sys.exit(0)

    def execute(self, cmd_line):
        """分配器：解析输入并调用对应函数"""
        parts = cmd_line.split()
        if not parts:
            return

        cmd_name = parts[0].lower()
        args = parts[1:]

        func = self.commands.get(cmd_name)
        if func:
            func(*args)
        else:
            print(f"未知命令: {cmd_name}。输入 'help' 查看帮助。")

# --- 新增管理界面逻辑 ---
def admin_console():
    """管理员命令行界面 - 采用命令模式封装"""
    session = PromptSession()
    admin_handler = AdminCommand()

    with patch_stdout():
        while True:
            try:
                cmd_line = session.prompt("admin > ").strip()
                if not cmd_line:
                    continue
                admin_handler.execute(cmd_line)

            except KeyboardInterrupt:
                # 处理 Ctrl+C
                print("\n[提示] 请输入 'quit' 退出或按 Ctrl+D 强制关闭。")
                continue
            except EOFError:
                # 处理 Ctrl+D
                print("\n强制退出...")
                break
            except Exception as e:
                print(f"[系统错误] 执行指令时发生异常: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        HOST = sys.argv[1]

    server_thread = threading.Thread(target=start_server_backend, daemon=True)
    server_thread.start()

    admin_console()