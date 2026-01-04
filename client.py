import asyncio
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


# 异步函数：负责接收消息
async def receive_messages(reader):
    while True:
        try:
            data = await reader.read(1024)
            if data:
                message = data.decode('utf-8')
                # 关键点：在 patch_stdout 环境下，print 会自动避让输入框
                print(f"{message}")
            else:
                print("\n[系统] 服务器关闭了连接。")
                break
        except Exception as e:
            print(f"\n[错误] 接收异常: {e}")
            break


# 异步函数：负责发送消息和处理 UI
async def main():
    if len(sys.argv) != 3:
        print("用法: python client.py [host] [port]")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    try:
        # 建立异步 TCP 连接
        reader, writer = await asyncio.open_connection(host, port)

        # 1. 处理身份验证
        username = input("请输入你的用户名: ").strip()
        writer.write(username.encode('utf-8'))
        await writer.drain()

        # 2. 创建 PromptSession 会话对象
        session = PromptSession()

        # 3. 启动接收协程
        receive_task = asyncio.create_task(receive_messages(reader))

        print(f"--- 已进入聊天室 (输入 '/quit' 退出) ---")

        # 4. 使用 patch_stdout 处理标准输出冲突
        with patch_stdout():
            while True:
                # 此时输入行会一直待在底部，收到的消息会自动排在它上面
                message = await session.prompt_async("请输入内容 > ")

                if message.strip() == "/quit":
                    writer.write("/quit".encode('utf-8'))
                    await writer.drain()
                    break

                if message.strip():
                    writer.write(message.encode('utf-8'))
                    await writer.drain()

        receive_task.cancel()
        writer.close()
        await writer.wait_closed()
        print("已断开连接。")

    except Exception as e:
        print(f"无法连接到服务器: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass