#!/usr/bin/env python
from sys import argv
from util import bcolors, timestamp

sysprint = __builtins__.print
__builtins__.print = lambda *args, **kwargs: sysprint(
  f'[{bcolors.OKGREEN}{timestamp()}{bcolors.ENDC}]',
  *args,
  **kwargs,
)

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
      print("[MAIN] Port %s is not working." %dev_port)
    else:
      is_reading, img = camera.read()
      w = camera.get(3)
      h = camera.get(4)
      if is_reading:
        print("[MAIN] Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
        working_ports.append(dev_port)
      else:
        print("[MAIN] Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
        available_ports.append(dev_port)
    dev_port +=1
  return available_ports,working_ports

def video():
  import cv2
  from imutils.video import VideoStream as Vs
  from camera.camera import apply_osd_content
  from time import sleep
  vs = Vs(int(argv[2]), False, (1920, 1080), 24).start()

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
  if len(argv) == 1:
    from uploaders.imupload import run_uploaders
    from web.flask_server import run_app
    run_app()
    run_uploaders()
  elif argv[1] == 'list':
    print('[MAIN] results:', list_ports())
  elif argv[1] == 'video':
    video()
  else:
    print('[MAIN] call using one of the following:')
    print('\t- List cameras: python main.py list')
    print('\t- Test camera:  python main.py video <cam_id>')
    print('\t- Run script:   python main.py')
