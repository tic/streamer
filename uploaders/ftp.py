import ftplib
from uploaders.common import Uploader

def verify_params(params: dict):
  try:
    params['host']
    params['username']
    params['password']
    params['path']
    return True
  except KeyError:
    print('[FTP] invalid ftp configuration; expected params: host, username, password, path')
    return False

def upload_file(uploader: Uploader, filename: str):
  try:
    print('[FTP] conducting upload')
    host = uploader.params['host']
    user = uploader.params['username']
    passwd = uploader.params['password']
    path = uploader.params['path']

    with open(filename, 'rb') as fp:
      with ftplib.FTP(host=host, user=user, passwd=passwd) as ftp:
        ftp.cwd(path)
        ftp.storbinary(f'STOR {filename}', fp)
    print('[FTP] done!')
  except Exception as err:
    print(f'[FTP] encountered error: {err}')
