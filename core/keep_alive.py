from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    return 'you lost the game'

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    #runs a server that gets pinged by UptimeRobot so that the bot doesn't shut off
    server = Thread(target=run)
    server.start()