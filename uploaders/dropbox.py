from dropbox import Dropbox
from uploaders.common import Uploader

def get_client(uploader: Uploader) -> Dropbox:
  client = Dropbox(uploader.params['token'])
  return client

def upload_file(uploader: Uploader, filename: str):
  print('[DROPBOX] conducting upload')
  try:
    client = get_client(uploader)
    with open(filename, 'rb') as fp:
      client.files_upload(fp.read(), f"{uploader.params['path']}/{filename}")
    print('[DROPBOX] done!')
  except Exception as err:
    print(f'[DROPBOX] encountered error: {err}')
