import socket as s
import re
import os

STATUS_200 = "HTTP/1.1 200 OK"
SPLIT = "\r\n"
CONTENT_SPLIT = SPLIT + SPLIT
ADDRESS = ("127.0.0.1",9989)

class HttpyServer:
    def __init__(self,host="127.0.0.1",port=9989,max_listeners=32,static_files="files"):
        self.socket = s.socket()
        self.host = host
        self.port = port
        self.max_listeners = max_listeners
        self.route_map = {}
        self.static_files = static_files

    def run(self):
        self.socket.bind((self.host,self.port))
        self.socket.listen(self.max_listeners)
        
        for i in range(3):
            client_sock, client_addr = self.socket.accept()
            msg = client_sock.recv(1024).decode().split(SPLIT) #also splits json data in post
            print(f"Received request from {client_addr}")
            route = self.get_route(msg[0])
            req_type = self.get_request_type(msg[0])
            response = ''
            if req_type=="GET":
                print("GET request!")
                path = self.static_files+route
                if os.path.exists(path) and (not route == '/'):
                    try:
                        #read as string
                        with open(path) as file:
                            response = file.read()
                    except:
                        #read as binary if cannot read as string
                        with open(path,'rb') as file:
                            response = file.read()
                #if the given route doesn't exist as a file.
                #check whether it exists in the route map
                elif route in self.route_map.keys():
                    #call the function
                    response = self.route_map[route]['GET']()
                else:
                    #if route doesn't exist, do nothing for now
                    pass

            elif req_type=="POST":
                print("POST request!")
                #data comes later in powershell
                #temp solution - check if continue is present in header
                data = ''
                if 'Expect: 100-continue' in msg:
                    data = client_sock.recv(1024).decode().split(SPLIT)
                else:
                    #if does not have expect, the data is bundled with the 1st request
                    #data always comes after ,''. So ,'', '' means no data (usually in get reqs)
                    divider = msg.index('') + 1 #+1 because we want the index after empty string
                    data = msg[divider:]
                    #if data[0] == '{':
                        #temp fix for broken json
                        #data = ''.join(data)
                    ####TEMPORARY
                    data = ''.join(data) #making so that data always is a string. temporary
                    ####
                    if route in self.route_map.keys():
                        #call the function
                        response = self.route_map[route]['POST'](data)
                    else:
                        #if route doesn't exist, do nothing for now
                        pass
            client_sock.sendall(self.resp(response))
            client_sock.close()


    def resp(self,data:str | bytes = ""):
        if type(data) == str:
            response = f'{STATUS_200}{SPLIT}Content-Length: {len(data)}{CONTENT_SPLIT}{data}'
            return response.encode()
        else:
            #if data is bytes
            response = f'{STATUS_200}{SPLIT}Content-Length: {len(data)}{CONTENT_SPLIT}'.encode()
            response = response + data
            return response
        
    def get_request_type(self,line:str) -> str:
        x = re.split("/",line,1) #splits at the first /
        request_type = x[0].strip()
        return request_type

    def get_route(self,line:str) -> str:
        req_type = self.get_request_type(line)
        route = line.replace(req_type,"").replace("HTTP/1.1","").strip()
        return route
    
app = HttpyServer()

def index():
    with open('files/index.html') as file:
        return file.read()
    
def hello_world():
    return "Hello world!"

def echo(data):
    return data

app.route_map = {
    '/':{
        'GET':index
    },
    '/helloworld':{
        'GET':hello_world
    },
    '/echo':{
        'POST':echo
    }
}

app.run()