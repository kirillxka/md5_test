import os
import hashlib
import uuid
import threading
import smtplib
import requests
from flask import Flask, request

app = Flask(__name__)


def download_file(id):
    url = tasks[id][0]
    response = requests.get(url)
    filename = os.path.basename(url)
    file_to_hash = open(filename, 'wb')
    for chunk in response.iter_content(100000):
        file_to_hash.write(chunk)
    file_to_hash.close()
    return filename


def find_hash(file):
    md5_hash = hashlib.md5()
    with open(file, 'rb') as f:
        content = f.read()
        md5_hash.update(content)
        return md5_hash.hexdigest()


def send_email(id, hash_sum):
    # User must replace login and password with exact values
    login = 'login'
    password = 'password'
    smtp_obj = smtplib.SMTP_SSL('smtp.mail.ru', 465)
    smtp_obj.ehlo()
    smtp_obj.login(login, password)
    url = tasks[id][0].encode('utf-8')
    email = tasks[id][1]
    body = 'URL: {}\nMD5: {}'.format(url, hash_sum)
    smtp_obj.sendmail(login, email, body)
    smtp_obj.quit()


def execute_task(id):
    filename = download_file(id)
    hash_sum = find_hash(filename)
    send_email(id, hash_sum)
    tasks[id][2] = 'done'
    tasks[id].append(hash_sum)


tasks = {}


@app.route('/submit', methods=['POST'])
def submit():
    url = request.args.get('url')
    email = request.args.get('email')
    id = str(uuid.uuid4())
    tasks[id] = [url, email, 'running']

    task_thread = threading.Thread(target=execute_task, args=[id])
    task_thread.start()

    return {'id': id}


@app.route('/check')
def check():
    id = request.args.get('id')
    url = tasks[id][0]
    if id in tasks:
        status = tasks[id][2]
        md5 = tasks[id][3]
        return {'md5': md5, 'status': status, 'url': url}
    else:
        return {'md5': None, 'status': 'task does not exist', 'url': url}


if __name__ == '__main__':
    app.run(debug=True)


