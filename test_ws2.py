import websocket
import json
import time

print('Connecting...')
ws = websocket.create_connection('ws://localhost:8001/ws/v2/testclient3', timeout=180)
print('Connected')

# Bekle connected mesajı için
r1 = ws.recv()
print('1:', r1[:100])

# Chat mesajı gönder
ws.send(json.dumps({'type': 'chat', 'message': 'Merhaba', 'complexity_level': 'simple'}))
print('Sent chat')

# Yanıtları al
for i in range(50):
    try:
        ws.settimeout(60)  # 60 saniye timeout
        r = ws.recv()
        data = json.loads(r)
        dtype = data.get('type', 'unknown')
        content = str(data.get('content', ''))[:100]
        print(f'{i}: type={dtype} content={content}')
        if dtype in ['end', 'error', 'stopped']:
            break
    except Exception as e:
        print(f'Error: {e}')
        break

ws.close()
print('Done')
