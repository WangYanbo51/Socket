import asyncio
import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


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


async def main():
    if len(sys.argv) != 3:
        path = os.path.relpath(sys.argv[0])
        if "py" in path:
            print(f"用法: python {path} [host] [port]")
        else:
            print(f"用法: ./{path} [host] [port]")
        return

    host = sys.argv[1]

    if not sys.argv[2].isdigit() or int(sys.argv[2]) >= 65536:
        print(f"'{sys.argv[2]}' 不是有效端口")
        exit(1)

    port = int(sys.argv[2])

    try:
        reader, writer = await asyncio.open_connection(host, port)

        while True:
            username = input("请输入你的用户名: ").strip()
            if not username:
                continue

            writer.write(username.encode('utf-8'))
            await writer.drain()

            response_data = await reader.read(1024)
            response = response_data.decode('utf-8').strip()

            if "__success__" in response:
                print(f"[系统] 欢迎你，{username}！验证成功。")
                break
            elif "__username_exist__" in response:
                print(f"[提示] 用户名 '{username}' 已被占用，请换一个。")
            else:
                print(f"[错误] 未知的验证响应: {response}")

        session = PromptSession()

        receive_task = asyncio.create_task(receive_messages(reader))

        print(f"--- 已进入聊天室 (输入 '/quit' 退出) ---")

        with patch_stdout():
            while True:
                message = await session.prompt_async(f"{username} > ")

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