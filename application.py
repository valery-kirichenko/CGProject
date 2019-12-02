import os
import uuid
import json
import re

from flask import Flask, render_template, request
import pika
from pymongo import MongoClient
from bson.objectid import ObjectId


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True




@app.route('/')
def index():
    ssh_key = os.environ.get('ssh_key')

    return render_template('index.html')


@app.route('/recognise', methods=['POST'])
def recognise():
    image = request.get_json()['image']
    task_id = ObjectId()

    credentials = pika.PlainCredentials('guest', os.environ.get('RABBIT_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='tasks')

    channel.basic_publish(exchange='',
                          routing_key='tasks',
                          body=json.dumps({'id': str(task_id), 'image': re.sub('^data:image/.+;base64,', '', image)}))
    return str(task_id)


@app.route('/results/<task_id>')
def result(task_id):
    client = MongoClient('localhost', 27017)
    db = client.image_recognition
    collection = db.results
    prediction = collection.find_one({'_id': ObjectId(task_id)})
    if prediction is None:
        return render_template('not_ready.html')
    else:
        return render_template('prediction.html', prediction=prediction['prediction'])
