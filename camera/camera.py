import numpy as np
import cv2
from threading import Lock as Mutex, Timer
from time import time, sleep
from PIL import Image
from datetime import datetime
from io import BytesIO as io_BytesIO
from subprocess import check_output as sp_check_output
from imutils.video import VideoStream as Vs
from re import search as re_search, match as re_match
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

    print(f'[CAMERA] cpu temp probe error: {err}')
    cpu_temp_value = 'T: UNAV'
  finally:
    if loop:
      Timer(config['image_upload']['save_interval'], cpu_temp_loop).start()

def get_image_intensity(frame: cv2.Mat):
  pixels = np.float32(frame.reshape(-1, 3))

  n_colors = 5
  criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
  flags = cv2.KMEANS_RANDOM_CENTERS

  _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
  _, counts = np.unique(labels, return_counts=True)
  dominant = palette[np.argmax(counts)]

  intensity: float = dominant.mean()
  return intensity.__round__(2)

def get_osd_content(osd_item: str, frame: cv2.Mat):
  if osd_item == 'time':
    return datetime.strftime(datetime.now(), '%D %H:%M:%S')

  if osd_item == 'cputemp':
    return str(cpu_temp_value)

  if osd_item == 'intensity':
    intensity = str(get_image_intensity(frame))
    while intensity[-3] != '.':
      intensity += '0'

    return f'I: {intensity}'

  return None

def apply_osd_content(frame, osd_items, osd_color):
  line = 0
  for item in osd_items:
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
      osd_color,
      1,
      cv2.LINE_AA
    )

  return frame

class Camera:
  def __init__(self, cam_id):
    camera = config['cameras'][cam_id]

    # Set up video reader
    self.Vs = Vs(cam_id, False, camera['resolution'], camera['fps']).start()

    # Other instance vars
    self.delta = 1.0 / camera['fps']
    self.res = camera['resolution']
    self.mode = camera['mode']
    self.osd = camera['osd']
    self.last_frame = 0
    self.saved_frame: cv2.Mat = None
    self.saved_frame_bytes: bytes = None
    self.mutex = Mutex()

    requested_rotation = camera['rotation']
    if (requested_rotation == '90'):
      self.rotation = cv2.ROTATE_90_CLOCKWISE
    elif (requested_rotation == '180'):
      self.rotation = cv2.ROTATE_180
    elif (requested_rotation == '270'):
      self.rotation = cv2.ROTATE_90_COUNTERCLOCKWISE
    else:
      self.rotation = None

  def __exit__(self):
    self.Vs.stop()

  def try_frame_update(self):
    try:
      with self.mutex:
        ctime = time()
        # If more than 1 frame's worth of time has elapsed get a new frame.
        if (ctime - self.last_frame > self.delta) or self.saved_frame is None:
          frame = self.Vs.read()

          self.last_frame = ctime
          frame: cv2.Mat = cv2.resize(frame, self.res, interpolation=cv2.INTER_AREA)

          # Adjust color if necessary
          if self.mode is not None:
            frame = cv2.cvtColor(frame, self.mode)

          # Apply rotation if necessary
          if self.rotation is not None:
            frame = cv2.rotate(frame, self.rotation)

          # Apply the OSD
          frame = apply_osd_content(frame, self.osd['items'], self.osd['color'])

          # Save the frame
          frame_out = Image.fromarray(frame, "RGB")
          buf = io_BytesIO()
          frame_out.save(buf, format='JPEG')
          self.saved_frame = frame
          self.saved_frame_bytes = buf.getvalue()
    except Exception as err:
      print(f'[CAMERA] frame update failed: {err}')

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
  cam_id_int = int(cam_id)
  try:
    cam_instance = cams[cam_id_int]
  except KeyError:
    cam_instance = Camera(cam_id_int)
    cams[cam_id_int] = cam_instance
  return cam_instance
