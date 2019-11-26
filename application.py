import os
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def index():
    ssh_key = os.environ.get('ssh_key')

    return render_template('index.html')