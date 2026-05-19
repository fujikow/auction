from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Servidor do Bot de Leilão Online."

def run():
    # Roda na porta 8080 (padrão para web services gratuitos)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()