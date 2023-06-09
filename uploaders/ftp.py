import ftplib
from datetime import datetime
from threading import Timer
from os import remove as os_remove
from config import config
from camera.camera import get_camera_instance, get_image_intensity

do_images_config = config['do_images']
camera_ids = do_images_config['cameras']
do_ftp = do_images_config['enabled'] is True
do_darkness_check = do_images_config['do_darkness_check'] is True
save_interval = do_images_config['save_interval']
darkness_threshold = do_images_config['darkness_threshold']
FTP_HOST = ''
FTP_USER = ''
FTP_PASSWD = ''
FTP_PATH = ''
if do_ftp:
  ftp_config = config['do_images']['ftp']
  FTP_HOST = ftp_config['host']
  FTP_USER = ftp_config['username']
  FTP_PASSWD = ftp_config['password']
  FTP_PATH = ftp_config['path']

def send_photos():
  if not do_ftp:
    return

  for camera_id in camera_ids:
    try:
      # Build the file name
      filename = datetime.strftime(datetime.now(), '%Y.%m.%dT%H.%M.%S') + f'-C{camera_id}' + '.jpeg'

      # Get camera instance
      camera_instance = get_camera_instance(camera_id)

      # Flush the first few frames.. sometimes it gets stuck
      camera_instance.flush()

      # Get an image
      frame = camera_instance.get_cv2_frame()

      # Do a darkness check, if required
      if do_darkness_check and get_image_intensity(frame) < darkness_threshold:
        print('[CAMERA] skipped FTP save -- frame too dark')
        return

      # Store image in temp file
      with open(filename, 'wb') as fp:
        fp.write(frame)

      # Send image to ftp server
      with open(filename, 'rb') as fp:
        with ftplib.FTP(host=FTP_HOST, user=FTP_USER, passwd=FTP_PASSWD) as ftp:
          ftp.cwd(FTP_PATH)
          ftp.storbinary(f'STOR {filename}', fp)
      os_remove(filename)
    except Exception as err:
      print(err)
    finally:
      Timer(save_interval, send_photos).start()