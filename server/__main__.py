import json
import socket
import argparse
from routes import get_server_routes
import logging
from server_log_config import setup_log_config


def sys_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-addr', default='')
    parser.add_argument('-port', default=7777)

    return parser


def make_answer(user_request):
    client_action = user_request.get('action')
    resolved_routes = list(
        filter(
            lambda itm: itm.get('action') == client_action, get_server_routes()
        )
    )

    route = resolved_routes[0] if resolved_routes else None

    if route:
        controller = route.get('controller')
        status_code = 200
        response_string = controller(user_request.get('data'))

    else:
        status_code = 400
        response_string = 'Action not supported'
        logging.error(f'Invalid user action {user_request}')

    request_json = json.dumps(
        {
            'response': status_code,
            'message': response_string
        }
    )

    if status_code == 200:
        logging.info(f'Prepared message for client {request_json}') 

    return request_json


def send_answer(clt, req_json):
    clt.send(req_json.encode('utf-8'))
    clt.close()


if __name__ == "__main__":
    parser = sys_arg_parser()
    args = parser.parse_args()

    sock = socket.socket()
    sock.bind((args.addr, int(args.port)))
    sock.listen(5)

    setup_log_config()
    
    logging.info(f'Server starts with host:{ args.addr } and port: { args.port }')
    while True:
        try:
            client, address = sock.accept()
            logging.info(f'Client detected {address}')
            data = client.recv(1024)
            logging.info(f'Message recieved from {address}')
            request = json.loads(
                data.decode('utf-8')
            )
            try:
                send_answer(client, make_answer(request))
                logging.info('Message sended!')
            except Exception as err:
                logging.error('Error sending answer!')
                sock.close()
        except KeyboardInterrupt:
            logging.info('Shutdown server')
            sock.close()


