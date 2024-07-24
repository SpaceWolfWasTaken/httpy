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
                while True:
                    data = client_sock.recv(1024)
                    self.breakdown(data)
                    data = self.send_data('Hi')
                    if not data:
                        pass
                    else:
                        client_sock.send(data)
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

    def breakdown(self,data:bytes):
        first_byte = data[0]
        fin = self.get_bit(first_byte,0)
        rsv1 = self.get_bit(first_byte,1)
        rsv2 = self.get_bit(first_byte,2)
        rsv3 = self.get_bit(first_byte,3)
        opcode = 0b00_001_111 & first_byte #basically removes the first 4 bits

        second_byte = data[1] & 0b01_111_111 #leaving out bit 0 since we need from byte 9-15 / 1-7
        #bit 0 is mask bit. we know its 1 from client->server data 
        payload_length = 0
        mask = []
        payload = []
        match second_byte:
            case 127:
                val = data[2]
                for i in range(3,6):
                    #basically - left shift till 8 bits are available, then add byte
                    val = val << 8 
                    val += data[i]
                payload_length = val
                mask = data[6:10]
                payload = data[10:]
            case 126:
                val = data[2]
                val = val << 8
                val += data[3]
                payload_length = val
                mask = data[4:8]
                payload = data[8:]
            case _:
                #for cases below 127
                #the byte contains payload length
                payload_length = second_byte
                mask = data[2:6]
                payload = data[6:]
        print(f'FIN: {fin}')
        print(f'RSV1: {rsv1}')
        print(f'RSV2: {rsv2}')
        print(f'RSV3: {rsv3}')
        print(f'OPCODE: {hex(opcode)}')
        print(f'Payload Length: {payload_length}')
        print(self.unmask(mask,payload).decode())
        
    def unmask(self, mask:bytes, payload:bytes) -> bytes:
        unmasked_vals = []

        for i,val in enumerate(payload):
            unmasked_vals.append(val ^ mask[i % 4])
        return bytes(unmasked_vals)


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
    
    def send_data(self, data:str | bytes):
        to_send = []
        payload = data
        first_byte = 0b10_000_001 #FIN is set to 1.
        if type(data) == str:
            first_byte = first_byte | 0b1  #Opcode is set to 0x1 = 0b1
            payload = payload.encode()
        else:
            first_byte = first_byte | 0b10  #Opcode is set to 0x2 = 0b10
        to_send.append(first_byte)

        payload_length = len(data)
        
        if payload_length <= 125:
            to_send.append(payload_length)
            to_send.extend(payload)
            return bytes(to_send)

        else:
            print("Server isn't configured for payloads above 125.")
            return False


