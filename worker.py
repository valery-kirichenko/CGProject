import pika
import base64
import json
import time
import os

from io import BytesIO
from keras.models import load_model
from keras.preprocessing.image import img_to_array
from PIL import Image
from pymongo import MongoClient
from bson.objectid import ObjectId


model = load_model('mnist99.h5')
model._make_predict_function()

credentials = pika.PlainCredentials('guest', os.environ.get('RABBIT_PASSWORD'))
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', credentials=credentials)))
tasks = connection.channel()
tasks.queue_declare(queue='tasks')


def callback(ch, method, properties, body):
    data = json.loads(body)
    print(' [*] Received message with id = ' + data['id'])
    image_data = base64.b64decode(data['image'])
    image = Image.open(BytesIO(image_data)).convert('L')
    img_array = img_to_array(image)
    img_array.astype('float32')
    img_array /= 255
    prediction = model.predict_classes(img_array.reshape(1, 784))[0]

    time.sleep(2)

    mongo_password = os.environ.get('MONGO_PASSWORD') 
    client = MongoClient(f'mongodb://worker:{mongo_password}@51.15.120.101/image_recognition', 27017)
    db = client.image_recognition
    collection = db.results
    collection.insert_one({'_id': ObjectId(data['id']), 'prediction': int(prediction)})


tasks.basic_consume(
    queue='tasks', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
tasks.start_consuming()
