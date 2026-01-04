import socket
import sys
import threading


def receive_messages(client_socket):
    """专门负责接收服务器消息的线程函数"""
    while True:
        try:
            # 持续监听服务器发来的消息
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"\r{message}")
                print("请输入内容: ", end="", flush=True)
            else:
                # 服务器关闭了连接
                break
        except:
            print("[错误] 与服务器断开连接。")
            break


def start_client():
    if len(sys.argv) != 3:
        print("用法: python client.py [host] [port]")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((host, port))

        # 1. 连接后立即处理身份验证（发送用户名）
        username = input("请输入你的用户名: ").strip()
        client.send(username.encode('utf-8'))

        # 2. 启动子线程：专门负责“收”
        # daemon=True 表示当主线程退出时，这个子线程也会自动随之关闭
        receive_thread = threading.Thread(target=receive_messages, args=(client,), daemon=True)
        receive_thread.start()

        # 3. 主线程负责“发”
        print(f"--- 已进入聊天室，输入 '/quit' 退出 ---")
        while True:
            message = input("")

            if message == "/quit":
                client.send("/quit".encode('utf-8'))
                break

            if message:
                client.send(message.encode('utf-8'))
                print("请输入内容: ", end="", flush=True)

    except ConnectionRefusedError:
        print("[错误] 无法连接到服务器。")
    finally:
        client.close()
        print("连接已关闭。")


if __name__ == "__main__":
    start_client()