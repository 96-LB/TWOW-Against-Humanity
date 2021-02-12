from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    #sets up a throwaway route for the flask app
    return 'you lost the game'

def run():
    #runs the flask app
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    #runs a server that gets pinged periodically so that the bot doesn't shut off
    server = Thread(target=run)
    server.start()