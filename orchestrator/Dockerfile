FROM python:3

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN mkdir /orchestrator
COPY orchestrator.py createvm_debian.yml runworker_debian.yml deletevm.yml hosts.template /orchestrator/

WORKDIR /orchestrator

CMD ["python3", "-u", "orchestrator.py"]
