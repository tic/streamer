from dropbox import Dropbox
from uploaders.common import Uploader

access_token = ''

def initial_setup_instructions():
  print('In browser: https://www.dropbox.com/oauth2/authorize?token_access_type=offline&response_type=code&client_id=<App key>')
  print('In terminal: curl https://api.dropbox.com/oauth2/token -d code=<received code> -d grant_type=authorization_code -u <App key>:<App secret>')
  print('Save access token from response')

def verify_params(params: dict):
  try:
    params['app_key']
    params['app_secret']
    params['refresh_token']
    params['path']
    return True
  except KeyError:
    print('[DROPBOX] invalid dropbox configuration; expected params: token, path')
    return False

def get_client(params: dict) -> Dropbox:
  global access_token
  client = Dropbox(
    oauth2_access_token=access_token,
    app_key=params['app_key'],
    app_secret=params['app_secret'],
    oauth2_refresh_token=params['refresh_token'],
  )

  access_token = client._oauth2_access_token
  return client

def upload_file(uploader: Uploader, filename: str):
  print('[DROPBOX] conducting upload')
  try:
    client = get_client(uploader.params)
    with open(filename, 'rb') as fp:
      client.files_upload(fp.read(), f"{uploader.params['path']}/{filename}")
    print('[DROPBOX] done!')
  except Exception as err:
    print(f'[DROPBOX] encountered error: {err}')
