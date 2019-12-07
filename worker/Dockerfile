FROM tensorflow/tensorflow:2.0.0-py3

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN mkdir /worker
COPY worker.py /worker/
COPY model.h5 /worker/

WORKDIR /worker

CMD ["python3", "-u", "worker.py"]
