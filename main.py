#!/usr/bin/env python
from config import config
from flask_server import app
from ftp import send_photos

if __name__ == '__main__':
  send_photos()
  app.run(host='0.0.0.0', port=config['port'], threaded=True)
