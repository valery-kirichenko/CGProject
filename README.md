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
2. Open worker source directory
   ```
   cd worker
   ```
3. Build docker image
   ```
   docker build -t worker .
   ```
4. Run docker image providing passwords as environment variables
   ```
   docker run -d -e RABBIT_PASSWORD -e MONGO_PASSWORD worker
   ```
