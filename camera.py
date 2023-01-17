import cv2
from threading import Lock as Mutex, Timer
from time import time, sleep
from PIL import Image
from datetime import datetime
from io import BytesIO as io_BytesIO
from subprocess import check_output as sp_check_output
from re import search as re_search, match as re_match
import numpy as np

from cv2 import Mat
from config import config

cpu_temp_value = 'T: LDNG'
def cpu_temp_loop():
  global cpu_temp_value
  loop = True
  try:
    output = sp_check_output(['vcgencmd', 'measure_temp'])
    output = output.decode('utf-8')
    val = re_search('temp=(\d+.\d+).*', output).group(1)
    cpu_temp_value = f'T: {val}'
  except Exception as err:
    if re_match(r".*No such file .* 'vcgencmd'", str(err)):
      print('[CAMERA] warning: system does not support cpu temperature probing')
      loop = False
      cpu_temp_value = 'T: UNSP'
      return
    
    print(err)
    cpu_temp_value = 'T: UNAV'
  finally:
    if loop:
      # Update the temperatures once per minute
      Timer(2.0, cpu_temp_loop).start()

def get_image_intensity(frame: Mat):
  pixels = np.float32(frame.reshape(-1, 3))

  n_colors = 5
  criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
  flags = cv2.KMEANS_RANDOM_CENTERS

  _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
  _, counts = np.unique(labels, return_counts=True)
  dominant = palette[np.argmax(counts)]
  
  intensity: float = dominant.mean()
  return intensity.__round__(2)

def get_osd_content(osd_item: str, frame: Mat):
  if osd_item == 'time':
    return datetime.strftime(datetime.now(), '%D %H:%M:%S')

  if osd_item == 'cputemp':
    return str(cpu_temp_value)
  
  if osd_item == 'brightness':
    intensity = get_image_intensity(frame)
    while intensity[-3] != '.':
      rounded_intensity += '0'
    
    return f'I: {intensity}'

  return None

class Camera:
  def __init__(self, cam_id):
    cameras = config['cameras']
    self.vc = cv2.VideoCapture(cam_id)
    self.delta = 1.0 / cameras[cam_id]['fps']
    self.res = cameras[cam_id]['resolution']
    self.mode = cameras[cam_id]['mode']
    self.osd = cameras[cam_id]['osd']
    self.last_frame = 0
    self.saved_frame: Mat = None
    self.saved_frame_bytes: bytes = None
    self.mutex = Mutex()

    requested_rotation = cameras[cam_id]['rotation']
    if (requested_rotation == '90'):
      self.rotation = cv2.ROTATE_90_CLOCKWISE
    elif (requested_rotation == '180'):
      self.rotation = cv2.ROTATE_180
    elif (requested_rotation == '270'):
      self.rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
    else:
      self.rotation = None

  def try_frame_update(self):
    try:
      with self.mutex:
        ctime = time()
        if (ctime - self.last_frame > self.delta) or self.saved_frame is None:
          # If more than 1 frame's worth of time has elapsed get a new frame.
          if not self.vc.isOpened():
            raise Exception("video stream closed unexpectedly")
          rval, frame = self.vc.read()
          if not rval:
            raise Exception("frame read failed")

          self.last_frame = ctime
          frame: Mat = cv2.resize(frame, self.res, interpolation=cv2.INTER_AREA)

          # Adjust color if necessary
          if self.mode is not None:
            frame = cv2.cvtColor(frame, self.mode)

          # Apply rotation if necessary
          if self.rotation is not None:
            frame = cv2.rotate(frame, self.rotation)

          # Apply the OSD
          line = 0
          for item in self.osd['items']:
            content = get_osd_content(item, frame)
            if content is None:
              continue

            position = (0, line * 20 + 18)
            line += 1
            frame = cv2.putText(
              frame,
              content,
              position,
              cv2.FONT_HERSHEY_SIMPLEX,
              0.60,
              self.osd['color'],
              1,
              cv2.LINE_AA
            )

          # Save the frame
          frame_out = Image.fromarray(frame, "RGB")
          buf = io_BytesIO()
          frame_out.save(buf, format='JPEG')
          self.saved_frame = frame
          self.saved_frame_bytes = buf.getvalue()
    except Exception as err:
      print('[{}] frame update failed: {}'.format(datetime.strftime(datetime.now(), '%H:%M:%S'), err))

  def get_bytes_frame(self):
    self.try_frame_update()
    return self.saved_frame_bytes
  
  def get_cv2_frame (self):
    self.try_frame_update()
    return self.saved_frame

  def flush(self):
    for _ in range(10):
      self.try_frame_update()
      sleep(self.delta)

cpu_temp_loop()
cams = {}
def get_camera_instance(cam_id):
  global cams
  try:
    cam_instance = cams[cam_id]
  except KeyError:
    cam_instance = Camera(cam_id)
    cams[cam_id] = cam_instance
  return cam_instance
