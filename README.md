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
1. Set IP address of server with RabbitMQ and MongoDB, and passwords for RabbitMQ, MongoDB and Azure by creating an env file. For example, `orchestrator.env`:
   ```
   RABBIT_PASSWORD=xxx
   MONGO_PASSWORD=xxx
   MASTER_IP=x.x.x.x
   AZURE_CLIENT_ID=xxx
   AZURE_SECRET=xxx
   AZURE_SUBSCRIPTION_ID=xxx
   AZURE_TENANT=xxx
   ```
2. Run docker image providing created file as `env_file` and a directory containing azure private (`azure`) and public (`azure.pub`) keys using bind mount:
   ```
   docker run -d --env-file orchestrator.env -v ~/.ssh/:/orchestrator/ssh/ valera5505/cgproject-orchestrator
   ```
