import socket as s
import re
import os
import sys
import threading

STATUS_200 = "HTTP/1.1 200 OK"
SPLIT = "\r\n"
CONTENT_SPLIT = SPLIT + SPLIT

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
        print(f"Running on http://{self.host}:{self.port}")
        print("Press CTRL+C to quit.")
        try:
            while True:
                self.req_resp()
        except Exception as e:
            print(e)
        finally:
            self.socket.close()
            sys.exit()

    def req_resp(self):
        client_sock, client_addr = self.socket.accept()
        msg = client_sock.recv(1024).decode().split(CONTENT_SPLIT)
        headers = msg[0].split(SPLIT) #first half contains header data
        print(f"Received request from {client_addr}")
        route = self.get_route(headers[0]) #first line is always {GET/POST,etc} /route HTTP/v
        req_type = self.get_request_type(headers[0])
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
                data = client_sock.recv(1024).decode()
            else:
                #if does not have expect, the data is bundled with the 1st request
                #so data comes after headers
                data = msg[1]
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
        route = line.replace(req_type,"").split("HTTP")[0].strip()
        return route
    

class ThreadedServer(HttpyServer):
    def __init__(self,host="127.0.0.1",port=9989,max_listeners=32,static_files="files"):
        super().__init__(host,port,max_listeners,static_files)
        self.thread_pool:set[threading.Thread] = set()


    def run(self):
        self.socket.bind((self.host,self.port))
        self.socket.listen(self.max_listeners)
        print(f"Running on http://{self.host}:{self.port}")
        print("Press CTRL+C to quit.")
        try:    
            dead_threads = set()
            while True:
                if len(self.thread_pool) < self.max_listeners:
                    thread = threading.Thread(target=self.req_resp,daemon=True)
                    thread.start()
                    self.thread_pool.add(thread)
                
                for thread in self.thread_pool:
                    if not thread.is_alive():
                        dead_threads.add(thread)
                if len(dead_threads) > 0:
                    self.thread_pool = self.thread_pool.difference(dead_threads)
                    dead_threads.clear()
                
        except Exception as e:
            print(e)
        finally:
            self.socket.close()
            sys.exit()


        