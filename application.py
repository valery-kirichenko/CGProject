import os
from flask import Flask, render_template, request
from keras.models import load_model
from PIL import Image
import re
from io import BytesIO
import base64
from keras.preprocessing.image import img_to_array


model = load_model('mnist99.h5')
model._make_predict_function()

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def index():
    ssh_key = os.environ.get('ssh_key')

    return render_template('index.html')


@app.route("/recognise", methods=["POST"])
def recognise():
    rq_image = request.get_json()['image']
    image_data = base64.b64decode(re.sub('^data:image/.+;base64,', '', rq_image))
    image = Image.open(BytesIO(image_data)).convert('L')
    img_array = img_to_array(image)
    img_array.astype('float32')
    img_array /= 255
    return str(model.predict_classes(img_array.reshape(1, 784))[0])

