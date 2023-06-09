from dotenv import load_dotenv
from os import getenv as os_getenv
from json import loads as json_loads
import cv2

load_dotenv()

def getenv(key: str, default='', alert_if_missing=False):
  value = os_getenv(key)
  if value is None:
    if alert_if_missing:
      print(f'[CONFIG] tried to access env variable "{key}" but it was not found')
    return default
  return value

config = {
  # Should be a byte-string suitable for use as a Flask secret.
  'secret': bytes(getenv('STREAMER_SECRET', '0000000000000000', alert_if_missing=True), 'utf-8'),

  # Specify valid logins via a 'username': 'password' dictionary.
  'logins': json_loads(getenv('STREAMER_LOGINS', '{}', alert_if_missing=True)),

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
    # 2: {
    #   'name': 'IR Camera',
    #   'fps': 24,
    #   'resolution': (856, 480),
    #   'mode': cv2.COLOR_BGR2RGB,
    #   'rotation': '0',
    #   'osd': {
    #     'color': (0, 0, 255),
    #     'items': ['time', 'intensity'],
    #   },
    # }
  },

  # Port to host the flask server on.
  'port': int(getenv('STREAMER_PORT', '8080')),

  # FTP configuration for saving images
  'do_images': {
    'enabled': getenv('STREAMER_DO_IMAGES') == 'true',
    'cameras': [0], # list of camera ids to save images for
    'offer_timelapse_downloads': getenv('STREAMER_OFFER_TIMELAPSE') == 'true',
    'ftp': json_loads(getenv('STREAMER_FTP_CONFIG', '{}', alert_if_missing=getenv('STREAMER_DO_IMAGES') == 'true')),
    'do_darkness_check': getenv('STREAMER_DO_DARKNESS_CHECK') == 'true',
    'darkness_threshold': float(getenv('STREAMER_DARKNESS_THRESHOLD', '0')),
    'save_interval': float(getenv('STREAMER_SAVE_INTERVAL', '1200.0'))
  },

  # Tweak aspects of the html pages
  'html': {
    'page_title': getenv('STREAMER_HTML_PAGE_TITLE', 'Budget Streamer'),
    'top_description': getenv('STREAMER_HTML_TOP_DESCRIPTION'),
    'bottom_html': getenv('STREAMER_HTML_BOTTOM_HTML'),
  },
}


