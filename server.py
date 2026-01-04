import socket
import threading

# 配置信息
HOST = socket.gethostname()
PORT = 9999

# 存储在线客户端的字典 {socket: username}
clients = {}
# 线程锁，防止多个线程同时操作 clients 字典导致崩溃
clients_lock = threading.Lock()


def broadcast(message, _sender_conn=None):
    """
    向所有在线客户端广播消息
    :param message: 要发送的字符串消息
    :param _sender_conn: 发送者的 socket。如果不为 None，则消息不会发回给发送者。
    """
    encoded_msg = message.encode('utf-8')

    with clients_lock:
        for conn in list(clients.keys()):
            # 过滤掉发送者本人，这样你在客户端发的消息，服务器就不会再回传给你了
            if conn != _sender_conn:
                try:
                    conn.send(encoded_msg)
                except:
                    # 如果发送失败，可能该客户端已断开，关闭并清理
                    conn.close()
                    if conn in clients:
                        del clients[conn]


def handle_client(conn, addr):
    """处理单个客户端连接的函数"""
    username = "未知用户"
    try:
        # 1. 握手阶段：接收客户端连接后的第一个消息（即用户名）
        username = conn.recv(1024).decode('utf-8')

        with clients_lock:
            clients[conn] = username

        # 通知所有人新用户加入
        welcome_msg = f"\n[系统提示] {username} 进入了聊天室。"
        print(f"[连接] {addr} 身份确认为: {username}")
        broadcast(welcome_msg)

        # 2. 消息循环阶段
        while True:
            # 阻塞等待接收消息
            data = conn.recv(1024).decode('utf-8')

            if not data or data == "/quit":
                break

            # 格式化消息并广播给除了发送者以外的所有人
            chat_msg = f"{username}: {data}"
            print(f"[消息] {chat_msg}")
            broadcast(chat_msg, _sender_conn=conn)

    except ConnectionResetError:
        print(f"[警告] {username} 的连接被重置。")
    except Exception as e:
        print(f"[错误] 处理 {username} 时出错: {e}")
    finally:
        # 3. 清理阶段：用户断开后的操作
        with clients_lock:
            if conn in clients:
                del clients[conn]

        conn.close()
        # 广播某人离开
        leave_msg = f"\n[系统提示] {username} 离开了聊天室。"
        broadcast(leave_msg)
        print(f"[退出] {username} 已断开。当前在线人数: {len(clients)}")


def start_server():
    """启动服务器"""
    # 创建 IPv4 TCP Socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 允许立即重用端口
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
    except socket.error as e:
        print(f"[失败] 无法绑定端口 {PORT}: {e}")
        return

    server.listen()
    print(f"[就绪] 服务器已在 {HOST}:{PORT} 启动，等待连接...")

    while True:
        # 等待新连接
        conn, addr = server.accept()

        # 为每个新连接创建一个线程
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        # 打印当前活跃线程数（减 1 是因为主线程本身也占一个）
        print(f"[系统] 当前在线人数: {threading.active_count() - 1}")


if __name__ == "__main__":
    start_server()