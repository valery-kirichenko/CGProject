from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World! This message was automatically deployed using CD"