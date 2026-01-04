import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if len(sys.argv) != 3:
    print("Usage: python client.py [host] [port]")
    exit(1)

host = sys.argv[1]
port = int(sys.argv[2])

s.connect((host, port))
msg = s.recv(1024)
s.close()

print(msg.decode())
