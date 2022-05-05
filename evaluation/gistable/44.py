#!/usr/bin/env python3

import wsgiref.simple_server

def app(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/plain')])
    return ['hello world'.encode('utf-8')]

def main():
    server = wsgiref.simple_server.make_server('0.0.0.0', 8000, app)
    server.serve_forever()

if __name__ == '__main__':
    main()