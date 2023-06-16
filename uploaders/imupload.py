from datetime import datetime
from threading import Timer
from os import remove as os_remove
from typing import List
from camera.camera import get_camera_instance, get_image_intensity
from config import config
from uploaders.common import Uploader

is_upload_enabled = config['image_upload']['enabled']
upload_config: List[Uploader] = config['image_upload']['uploader_config']
camera_ids = config['image_upload']['camera_ids']
do_darkness_check = config['image_upload']['do_darkness_check']
darkness_threshold = config['image_upload']['darkness_threshold']
save_interval = config['image_upload']['save_interval']

def send_photo(filename: str):
  for uploader in upload_config:
    try:
      uploader.execute(filename)
    except Exception as err:
      print(f'[IMUPLOAD] unexpected uploader failure in uploader "{uploader.type}": {err}')

def upload_loop():
  print('[IMUPLOAD] running uploaders')
  for camera_id in camera_ids:
    print(f'[IMUPLOAD] uploading from camera id {camera_id}')
    try:
      # Build the file name
      filename = datetime.strftime(datetime.now(), '%Y.%m.%dT%H.%M.%S') + f'-C{camera_id}' + '.jpeg'

      # Get camera instance
      camera_instance = get_camera_instance(camera_id)

      # Flush the first few frames.. sometimes it gets stuck
      camera_instance.flush()

      # Get an image
      frame = camera_instance.get_bytes_frame()

      # Do a darkness check, if required
      if do_darkness_check and get_image_intensity(camera_instance.get_cv2_frame()) < darkness_threshold:
        print(f'[IMUPLOAD] skipped upload of {filename} -- frame too dark')
        return

      # Store image in temp file
      with open(filename, 'wb') as fp:
        fp.write(frame)

      # Send image to uploaders
      send_photo(filename)

      # Clean up the temp file
      os_remove(filename)
    except Exception as err:
      print(f'[IMUPLOAD] unexpected frame capture error: {err}')
    finally:
      print(f'[IMUPLOAD] upload iteration complete')
      Timer(save_interval, upload_loop).start()

def run_uploaders():
  if is_upload_enabled:
    Timer(0, upload_loop).start()
  else:
    print('[IMUPLOAD] image uploading is disabled')

