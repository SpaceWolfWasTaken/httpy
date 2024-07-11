import socket as s

STATUS_200 = "HTTP/1.1 200 OK"
SPLIT = "\r\n"
CONTENT_SPLIT = SPLIT + SPLIT
ADDRESS = ("127.0.0.1",9989)

sock = s.socket()
sock.bind(ADDRESS)
sock.listen(5)

#client_socket, client_addr = sock.accept()

def empty():
    data = '''
    <html>
    <head> <title> Empty </title> </head>
    <body>
    <h1> This is an empty HTML page </h1>
    </body>
    </html>
    '''
    response = f'{STATUS_200}{SPLIT}Content-Length: {len(data)}{CONTENT_SPLIT}{data}'
    return response

def respond(c:tuple[s.socket, tuple[str,int]]):
    sock, addr = c
    msg = sock.recv(1024).decode().split(SPLIT)
    print(f"Received request from {addr}")
    sock.sendall(empty().encode())

respond(sock.accept())
sock.close()
