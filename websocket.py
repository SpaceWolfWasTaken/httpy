import socket as s
import base64
import hashlib
import sys

class WebSocket:
    def __init__(self, host="127.0.0.1",port=9989,max_listeners=32):
        self.socket = s.socket()
        self.host = host
        self.port = port
        self.max_listeners = max_listeners
        self.clients = dict()
        
    def run(self):
        self.socket.bind((self.host,self.port))
        self.socket.listen(self.max_listeners)
        print(f"Running on ws://{self.host}:{self.port}")
        print("Press CTRL+C to quit.")
        try:    
            client_sock, client_addr = self.socket.accept()
            if self.handshake(client_sock):
                data = client_sock.recv(1024)
                pass
            else:
                #if first msg is not about ws upgrade
                client_sock.close()
                
        except Exception as e:
            print(e)
        finally:
            self.socket.close()
            sys.exit()

    def handshake(self,client) -> bool:
        try:
            data = client.recv(1024)
            data = data.decode().split("\r\n")
            ws_key = ""
            for i in data:
                if "Sec-WebSocket-Key" in i:
                    ws_key = i.replace("Sec-WebSocket-Key:","").strip()
                    break
            key = self.hash_key(ws_key)
            res = f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {key}\r\n\r\n"
            
            client.send(res.encode())
            return True
        except:
            return False

    def hash_key(self,key:str):
        #based on https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Sec-WebSocket-Accept
        key = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        key = hashlib.sha1(key.encode()).digest() #digest is used to get hash in bytes form
        key = base64.b64encode(key)
        #brute forcing to get the key as string
        key = str(key) #done to force the hash value to act as string
        key = key[2:-1] #removes b' and '.
        return key

    
