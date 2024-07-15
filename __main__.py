from server import HttpyServer

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