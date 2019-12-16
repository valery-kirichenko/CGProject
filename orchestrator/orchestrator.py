import os
import random
import subprocess
import string
import re
import sys
import time
from datetime import datetime

from pymongo import MongoClient
import pika


mongo_password = os.environ.get('MONGO_PASSWORD')
rabbit_password = os.environ.get('RABBIT_PASSWORD')
master_ip = os.environ.get('MASTER_IP')
environ_error = False

if mongo_password is None or rabbit_password is None:
    print('Please set both MONGO_PASSWORD and RABBIT_PASSWORD env variables')
    environ_error = True
if not all(k in os.environ for k in ('AZURE_CLIENT_ID', 'AZURE_SECRET', 'AZURE_SUBSCRIPTION_ID', 'AZURE_TENANT')):
    print('Please set all env variables for Azure (AZURE_CLIENT_ID, AZURE_SECRET, AZURE_SUBSCRIPTION_ID, AZURE_TENANT)')
    environ_error = True
if master_ip is None:
    print('Please set MASTER_IP env variable to a server containing MongoDB and RabbitMQ')
    environ_error = True
if environ_error:
    sys.exit(1)


def get_mongo_db():
    client = MongoClient(f'mongodb://worker:{mongo_password}@{master_ip}/image_recognition', 27017)
    return client.image_recognition


def random_id(length=6):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def createvm(vm_id=None):
    if vm_id is None:
        vm_id = random_id()

    print(f'\033[92mCreating\033[0m VM with id: \033[1m{vm_id}\033[0m')
    create_time = time.time()
    create_result = subprocess.run(['ansible-playbook', 'createvm_debian.yml', '--extra-vars', 'vmID=' + vm_id], capture_output=True)
    print(f'VM creation exited with return code: {create_result.returncode} ({"un" if create_result.returncode != 0 else ""}successful)')
    if create_result.returncode != 0:
        print('=> STDOUT:')
        print(create_result.stdout.decode('utf-8'))
        print('=> STDERR:')
        print(create_result.stderr.decode('utf-8'))
        return
    vm_ip = re.findall(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        create_result.stdout.decode('utf-8'))[0]
    print(f'Created VM with IP: {vm_ip} ({int(time.time() - create_time)}s)')
    spawn_time = int(time.time())

    with open(f'hosts.template') as template_file:
        template = template_file.read().replace('IP_ADDRESS', vm_ip)
        with open(f'hosts_{vm_id}.ini', 'w') as hosts:
            hosts.write(template)

    print(f'Setting up the VM...')

    setup_time = time.time()
    setup_result = subprocess.run(['ansible-playbook', '-i', f'hosts_{vm_id}.ini', 'runworker_debian.yml'], capture_output=True)
    print(f'VM setup exited with return code: {setup_result.returncode} ' \
        f'({"un" if setup_result.returncode != 0 else ""}successful, {int(time.time() - setup_time)}s)')

    if setup_result.returncode != 0:
        print('=> STDOUT:')
        print(setup_result.stdout.decode('utf-8'))
        print('=> STDERR:')
        print(setup_result.stderr.decode('utf-8'))
        deletevm(vm_id)
    else:
        collection = get_mongo_db().workers
        collection.insert_one({'worker_id': vm_id, 'worker_ip': vm_ip, 'spawn_time': spawn_time})

    os.remove(f'hosts_{vm_id}.ini')


def deletevm(vm_id):
    print(f'Deleting VM with id: \033[1m{vm_id}\033[0m')
    delete_result = subprocess.run(['ansible-playbook', 'deletevm.yml', '--extra-vars', 'vmID=' + vm_id], capture_output=True)
    print(f'VM deletion exited with return code: {delete_result.returncode} ({"un" if delete_result.returncode != 0 else ""}successful)')

    if delete_result.returncode == 0:
        collection = get_mongo_db().workers
        collection.delete_one({'worker_id': vm_id})


def get_active_workers():
    return list(get_mongo_db().workers.find({}))


def latest_activity(worker_ip):
    collection = get_mongo_db().results
    try:
        return collection.find({'worker': worker_ip}, {'time': 1}).sort([('time', -1)]).limit(1).next()['time']
    except StopIteration:
        return 0


def number_of_tasks():
    credentials = pika.PlainCredentials('guest', rabbit_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=f'{master_ip}', credentials=credentials))
    tasks = connection.channel()
    return tasks.queue_declare(queue='tasks', passive=True).method.message_count


def should_delete_worker(spawn_time, latest_activity):
    current_time = int(time.time())
    alive_for = current_time - spawn_time
    no_activity_for = current_time - latest_activity
    print(f'    Was alive for {(alive_for / 60):.2f} minutes ({(alive_for / 3600):.2f} hours)')
    print(f'    Latest activity was {(no_activity_for / 60):.2f} minutes ago')

    # if the machine is alive for more than 5 minutes and there was no activity for 2 minutes, delete
    if alive_for/60 % 60 > 5 and no_activity_for/60 > 2:
        return True
    else:
        return False


if __name__ == '__main__':
    waiting_times = {30: 15, 15: 10, 5: 5}
    while True:
        workers_deleted = 0
        current_time = int(time.time())
        # sort workers by their closeness to the end of hour
        workers = sorted(get_active_workers(), key=lambda x: (current_time - x['spawn_time'])/60 % 60, reverse=True)
        tasks_in_queue = number_of_tasks()
        are_vms_needed = tasks_in_queue > 0
        print(f'Current time: {datetime.now().time()}\nActive workers: {len(workers)}\nWorkers needed: {are_vms_needed} ({tasks_in_queue} tasks)')
        if are_vms_needed and len(workers) == 0:
            createvm()
        if not are_vms_needed:
            for vm in workers:
                print(f'Checking worker \033[94m{vm["worker_id"]}\033[0m:')
                if should_delete_worker(vm['spawn_time'], latest_activity(vm['worker_ip'])):
                    print('=> \033[93mDeleting\033[0m this worker')
                    deletevm(vm['worker_id'])
                    workers_deleted += 1
                else:
                    print('=> \033[92mKeeping\033[0m this worker alive')

        print()
        # do not make pauses if all workers were deleted in case new task was made
        if workers_deleted == len(workers) and workers_deleted > 0:
            continue
        for label in waiting_times:
            print(f'Next check in {label}s...')
            time.sleep(waiting_times[label])
        print()
