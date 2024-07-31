import socket as s
import base64
import hashlib
import sys

class WebSocket:
    def __init__(self, host="127.0.0.1",port=9989,max_listeners=32, buffer=1024):
        self.socket = s.socket()
        self.host = host
        self.port = port
        self.max_listeners = max_listeners
        self.clients = dict()
        self.buffer = buffer
        
    def run(self):
        self.socket.bind((self.host,self.port))
        self.socket.listen(self.max_listeners)
        print(f"Running on ws://{self.host}:{self.port}")
        print("Press CTRL+C to quit.")
        try:    
            client_sock, client_addr = self.socket.accept()
            if self.handshake(client_sock):
                while True:
                    data = client_sock.recv(self.buffer)
                    frame = Frame(data[0])
                    if frame.opcode == 8:
                        print('Connection closing...')
                        client_sock.close()
                        sys.exit()
                    payload = Payload(data,frame.opcode)
                    frame.display()
                    for _ in range(int(payload.payload_length / self.buffer)):
                        data = client_sock.recv(self.buffer)
                        payload.payload.extend(data)
                    content = payload.unmask()
                    print(content.decode())
                    
                    
                    
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
    
    def send_data(self, data:str | bytes):
        to_send = []
        payload = data
        first_byte = 0b10_000_000 #FIN is set to 1.
        if type(data) == str:
            first_byte = first_byte | 0b1  #Opcode is set to 0x1 = 0b1
            payload = payload.encode()
        else:
            first_byte = first_byte | 0b10  #Opcode is set to 0x2 = 0b10

        to_send.append(first_byte)

        payload_length = len(data)
        print(f"Sending data of length: {payload_length}")
        
        if payload_length <= 125:
            to_send.append(payload_length)

        elif payload_length <=65535:
            to_send.append(126)
            payload_length = payload_length.to_bytes(2,'big')
            to_send.extend(payload_length)

        else:
            to_send.append(127)
            payload_length = payload_length.to_bytes(8,'big')
            to_send.extend(payload_length)
        
        to_send.extend(payload)

        return bytes(to_send)


class Frame:
    def __init__(self, first_byte):
        self.fin = 0
        self.rsv1 = 0
        self.rsv2 = 0
        self.rsv3 = 0
        self.opcode = 0
        self.load(first_byte)

    def load(self,byte:int):
        self.fin = self.get_bit(byte,0)
        self.rsv1 = self.get_bit(byte,1)
        self.rsv2 = self.get_bit(byte,2)
        self.rsv3 = self.get_bit(byte,3)
        self.opcode = 0b00_001_111 & byte

    def get_bit(self, data:int, pos:int) -> int:
        '''
        if data & a = a,
        bit is 1,
        else bit is 0
        '''
        mask = 0b1 << (7-pos) #1st pos is 7-0 = 0b10_000_000 #2nd pos is 7-1 = 0b1_000_000
        if (data & mask): #if bit is set
            return 1
        else:
            return 0
        
    def display(self):
        print(f'FIN: {self.fin}')
        print(f'RSV1: {self.rsv1}')
        print(f'RSV2: {self.rsv2}')
        print(f'RSV3: {self.rsv3}')
        print(f'OPCODE: {hex(self.opcode)}')

        
class Payload:
    def __init__(self, data:bytes, opcode:int):
        self.payload_length = 0
        self.mask = []
        self.payload = []
        self.is_masked = True
        self.opcode = opcode
        self.first_frame_unload(data)

    def first_frame_unload(self, data):
        second_byte = data[1] & 0b01_111_111 #leaving out bit 0 since we need from byte 9-15 / 1-7
        #bit 0 is mask bit. we know its 1 from client->server data 
        payload = []
        match second_byte:
            case 127:
                val = data[2]
                for i in range(3,10):
                    #basically - left shift till 8 bits are available, then add byte
                    val = val << 8 
                    val += data[i]
                self.payload_length = val
                self.mask = data[10:14]
                payload = data[14:]
                print('case 127')
            case 126:
                val = data[2]
                val = val << 8
                val += data[3]
                self.payload_length = val
                self.mask = data[4:8]
                payload = data[8:]
                print('case 126')
            case _:
                #for cases below 127
                #the byte contains payload length
                self.payload_length = second_byte
                self.mask = data[2:6]
                payload = data[6:]
                print('case <=125')
        self.payload.extend(payload)

    def add(self, data):
        self.payload.extend(data)

    def unmask(self):
        if self.is_masked:
            unmasked_vals = []
            for i,val in enumerate(self.payload):
                unmasked_vals.append(val ^ self.mask[i % 4])
            return bytes(unmasked_vals)

    