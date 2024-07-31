'''
import server, time

app = server.ThreadedServer(max_listeners=2)

def index():
    with open('files/index.html') as file:
        return file.read()
    
def hello_world():
    return "Hello world!"

def echo(data):
    return data

def sleep():
    time.sleep(5)
    print("Slept for 5 seconds.")
    return "Slept for 5 seconds."

app.route_map = {
    '/':{
        'GET':index
    },
    '/helloworld':{
        'GET':hello_world
    },
    '/echo':{
        'POST':echo
    },
    '/sleep':{
        'GET':sleep
    }
}

app.run()
'''
import websocket
app = websocket.ThreadedWebSocket(buffer=4096,max_listeners=2)

def text(content):
    print("Text received: ")
    print(content)

def binary(content):
    print("Binary received.")

app.text_callback = text
app.binary_callback = binary
app.run()