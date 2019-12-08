# How to run
**Warning.** WIP, some variables (like IP addresses) are hard-coded

## Web interface
You should have RabbitMQ and MongoDB installed on this server

1. Set passwords for RabbitMQ and MongoDB:
   ```
   export RABBIT_PASSWORD=securepassword MONGO_PASSWORD=differentpassword
   ```
2. Open app source directory:
   ```
   cd application
   ```
3. Install requirements:
   ```
   pip3 install -r requirements.txt
   ```
4. Run flask app as usual:

   `FLASK_APP=application.py flask run` or `gunicorn application:app`

## Worker
1. Set passwords for RabbitMQ and MongoDB
   ```
   export RABBIT_PASSWORD=securepassword MONGO_PASSWORD=differentpassword
   ```
2. Run docker image providing passwords as environment variables
   ```
   docker run -d -e RABBIT_PASSWORD -e MONGO_PASSWORD valera5505/cgproject-worker
   ```

## Orchestrator
1. Set passwords for RabbitMQ, MongoDB and Azure
   ```
   export RABBIT_PASSWORD=xxx MONGO_PASSWORD=xxx AZURE_CLIENT_ID=xxx AZURE_SECRET=xxx AZURE_SUBSCRIPTION_ID=xxx AZURE_TENANT=xxx
   ```
2. Run docker image providing passwords as environment variables and a directory containing azure private (`azure`) and public (`azure.pub`) keys using bind mount:
   ```
   docker run -d -e RABBIT_PASSWORD -e MONGO_PASSWORD -e AZURE_CLIENT_ID -e AZURE_SECRET -e AZURE_SUBSCRIPTION_ID -e AZURE_TENANT -v ~/.ssh/:/orchestrator/ssh/ valera5505/cgproject-orchestrator
   ```
