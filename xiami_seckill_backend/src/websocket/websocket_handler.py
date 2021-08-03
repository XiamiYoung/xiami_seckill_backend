import json
from controllers.public.jd import jd_controller

class BackendWebSocketConsumer():
    async def handle_request(self, scope, receive, send):
        while True:
            event = await receive()
            if event['type'] == 'websocket.connect':
                await send({
                    'type': 'websocket.accept'
                })

            if event['type'] == 'websocket.disconnect':
                break

            if event['type'] == 'websocket.receive':
                req_body = event['text']
                req_body = json.loads(req_body)
                if req_body['type'] == 'check_qr_result':
                    await send({
                        'type': 'websocket.send',
                        'text': 'await jd_controller.ws_check_result(req_body)'
                    })