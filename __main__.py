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
app = websocket.WebSocket(buffer=4096)
app.run()