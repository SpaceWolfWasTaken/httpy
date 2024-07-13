import socket as s
import re

STATUS_200 = "HTTP/1.1 200 OK"
SPLIT = "\r\n"
CONTENT_SPLIT = SPLIT + SPLIT
ADDRESS = ("127.0.0.1",9989)

sock = s.socket()
sock.bind(ADDRESS)
sock.listen(5)

def resp(data=""):
    response = f'{STATUS_200}{SPLIT}Content-Length: {len(data)}{CONTENT_SPLIT}{data}'
    return response


def get_request_type(line:str) -> str:
    x = re.split("/",line,1) #splits at the first /
    request_type = x[0].strip()
    return request_type

def get_route(line:str) -> str:
    req_type = get_request_type(line)
    route = line.replace(req_type,"").replace("HTTP/1.1","").strip()
    return route

for i in range(4):
    client_sock, client_addr = sock.accept()
    #data comes here in cmd. tf
    msg = client_sock.recv(1024).decode().split(SPLIT) #also splits json data in post
    print(f"Received request from {client_addr}")
    #print(msg)
    route = get_route(msg[0])
    req_type = get_request_type(msg[0])
    
    print(f'Route: {route}')
    if req_type=="GET":
        print("GET request!")
    elif req_type=="POST":
        print("POST request!")
        #data comesd later in powershell
        #temp solution - check if continue is present in header
        if 'Expect: 100-continue' in msg:
            data = client_sock.recv(1024).decode().split(SPLIT)
            print(data)
        else:
            #if does not have expect, the data is bundled with the 1st request
            #data always comes after ,''. So ,'', '' means no data (usually in get reqs)
            divider = msg.index('') + 1 #+1 because we want the index after empty string
            data = msg[divider:]
            print(data)
        #need to serialize differently based on Content-Type

    client_sock.sendall(resp().encode())
    client_sock.close()