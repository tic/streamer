import ftplib
from datetime import datetime
from threading import Timer
from os import remove as os_remove
from config import config
from camera import get_camera_instance

do_images_config = config['do_images']
camera_ids = config['do_images']['cameras']
do_ftp = do_images_config['enabled'] is True
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
      for _ in range(5):
        camera_instance.get_frame()

      # Get an image
      frame = camera_instance.get_frame()

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
      Timer(1200.0, send_photos).start()
