import websocket
import json
import time

ws = websocket.create_connection('ws://localhost:8001/ws/v2/testclient2', timeout=120)
print('Connected')

# Bekle connected mesajı için
r1 = ws.recv()
print('1:', r1[:100])

# Chat mesajı gönder
ws.send(json.dumps({'type': 'chat', 'message': 'Merhaba'}))
print('Sent chat')

# Yanıtları al
for i in range(30):
    try:
        ws.settimeout(15)
        r = ws.recv()
        data = json.loads(r)
        dtype = data.get('type', 'unknown')
        content = str(data.get('content', ''))[:50]
        print(f'{i}: type={dtype} content={content}')
        if dtype == 'end':
            break
    except Exception as e:
        print(f'Error: {e}')
        break

ws.close()
print('Done')
