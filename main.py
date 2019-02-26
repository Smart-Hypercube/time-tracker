from asyncio import get_event_loop
import json
import pickle
from random import random, seed
from requests import post

API = 'https://api.telegram.org'


def update():
    response = post(f'{API}/bot{token}/getUpdates', {'offset': data['offset']}, timeout=10).json()
    if not response['ok']:
        print('getUpdates', response)
        return
    for update in response['result']:
        data['offset'] = max(data['offset'], update['update_id']) + 1
        if 'message' not in update:
            continue
        message = update['message']
        if message['chat']['id'] != data['user']:
            continue
        if 'text' not in message:
            continue
        text = message['text'].strip()
        if not text:
            continue
        data['log'].append({'time': message['date'], 'content': text, 'p': data['p']})
        log = {}
        for i in data['log']:
            log.setdefault(i['content'], 0)
            log[i['content']] += 1 / i['p']
        activities = sorted(log)
        text = '\n'.join(f'{k}: {round(log[k] / 3600)} hrs' for k in activities)
        keyboard = {'keyboard': [activities[i:i + 3] for i in range(0, len(activities), 3)]}
        keyboard = json.dumps(keyboard)
        response = post(f'{API}/bot{token}/sendMessage', {
            'chat_id': data['user'],
            'text': text,
            'disable_notification': True,
            'reply_to_message_id': message['message_id'],
            'reply_markup': keyboard,
        }, timeout=10).json()
        if not response['ok']:
            print('sendMessage', response)
    with open('data.pickle', 'wb') as f:
        pickle.dump(data, f)


def send():
    try:
        post(f'{API}/bot{token}/sendMessage', {'chat_id': data['user'], 'text': 'What are you doing now?'}, timeout=10)
    except:
        loop.call_soon(send)


def each_minute(t):
    loop.call_at(t + 60, each_minute, t + 60)
    seed()
    for i in range(60):
        if random() < data['p']:
            loop.call_at(t + i, send)
    try:
        update()
    except:
        pass


if __name__ == '__main__':
    with open('token.txt') as f:
        token = f.read().strip()
    try:
        with open('data.pickle', 'rb') as f:
            data = pickle.load(f)
    except OSError:
        data = {'offset': 0, 'user': 164648654, 'p': 0.0002, 'log': []}
    loop = get_event_loop()
    start = loop.time()
    loop.call_soon(each_minute, start)
    loop.run_forever()
