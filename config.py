from dotenv import load_dotenv
from os import getenv as os_getenv
from json import loads as json_loads
import cv2

from uploaders.common import Uploader

load_dotenv()

def getenv(key: str, default='', alert_if_missing=False, json=False):
  rval = default
  value = os_getenv(key)
  if value is None:
    if alert_if_missing:
      print(f'[CONFIG] tried to access env variable "{key}" but it was not found')
  else:
    rval = value

  return json_loads(rval) if json else rval

config = {
  # Camera configuration.
  'cameras': {
    0: {
      'name': 'Integrated Camera',
      'fps': 24,
      'resolution': (640, 480),
      'mode': cv2.COLOR_BGR2RGB,
      'rotation': '0',
      'osd': {
        'color': (0, 255, 0),
        'items': ['time', 'cputemp', 'intensity'],
      },
    },
  },

  # FTP configuration for saving images
  'image_upload': {
    'enabled': getenv('STREAMER_DO_IMAGE_UPLOAD') == 'true',
    'camera_ids': getenv('STREAMER_IMAGE_UPLOAD_CAMERA_IDS', '[]', alert_if_missing=getenv('STREAMER_DO_IMAGES') == 'true', json=True),
    'offer_timelapse_downloads': getenv('STREAMER_OFFER_TIMELAPSE') == 'true',
    'uploader_config': [Uploader(**i) for i in getenv('STREAMER_UPLOAD_CONFIG', '{}', alert_if_missing=getenv('STREAMER_DO_IMAGES') == 'true', json=True)],
    'do_darkness_check': getenv('STREAMER_DO_DARKNESS_CHECK') == 'true',
    'darkness_threshold': float(getenv('STREAMER_DARKNESS_THRESHOLD', '0')),
    'save_interval': float(getenv('STREAMER_SAVE_INTERVAL', '1200.0'))
  },

  # Control the web server
  'web': {
    'enabled': getenv('STREAMER_DO_HTML_PAGE') == 'true',
    'port': int(getenv('STREAMER_PORT', '8080')),
    'secret': bytes(getenv('STREAMER_SECRET', '0000000000000000', alert_if_missing=True), 'utf-8'),
    'logins': json_loads(getenv('STREAMER_LOGINS', '{}', alert_if_missing=True)),
    'page_title': getenv('STREAMER_HTML_PAGE_TITLE', 'Budget Streamer'),
    'top_description': getenv('STREAMER_HTML_TOP_DESCRIPTION'),
    'bottom_html': getenv('STREAMER_HTML_BOTTOM_HTML'),
  },
}


