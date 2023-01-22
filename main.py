#!/usr/bin/env python
from config import config
from flask_server import app
from ftp import send_photos
from sys import argv

"""
Test the ports and returns a tuple with the available ports and the ones that are working.
"""
def list_ports():
  import cv2
  is_working = True
  dev_port = 0
  working_ports = []
  available_ports = []
  while is_working:
    camera = cv2.VideoCapture(dev_port)
    if not camera.isOpened():
      is_working = False
      print("Port %s is not working." %dev_port)
    else:
      is_reading, img = camera.read()
      w = camera.get(3)
      h = camera.get(4)
      if is_reading:
        print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
        working_ports.append(dev_port)
      else:
        print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
        available_ports.append(dev_port)
    dev_port +=1
  return available_ports,working_ports

def video():
  import cv2
  from imutils.video import VideoStream as Vs
  from camera import apply_osd_content
  from time import sleep
  vs = Vs(2, False, (1920, 1080), 24).start()

  try:
    while True:
      frame = vs.read()
      frame = cv2.resize(frame, (640, 480))
      frame = apply_osd_content(frame, ['time', 'intensity'], (0, 0, 255))
      cv2.imshow("out", frame)
      sleep(1 / 60)
      cv2.waitKey(1)
  except KeyboardInterrupt:
    pass

  vs.stop()
  cv2.destroyAllWindows()

if __name__ == '__main__':
  if 'list' in argv:
    print(list_ports())
  elif 'video' in argv:
    video()
  else:
    send_photos()
    app.run(host='0.0.0.0', port=config['port'], threaded=True)
