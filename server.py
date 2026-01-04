import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = socket.gethostname()
port = 9999

server.bind((host, port))
server.listen(5)

while True:
    conn, addr = server.accept()

    print("Connected by", addr)
    Message = 'Welcome to My Server\r\n'

    conn.send(Message.encode('utf-8'))
    conn.close()