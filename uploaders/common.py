from importlib import import_module

class UploaderError(Exception):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class Uploader:
  type: str
  params: dict

  def __init__(self, type: str, params: dict):
    self.type = type
    self.params = params

    if not self.__verify_params__():
      raise UploaderError(f'invalid uploader configuration for type "{type}"')

  def __verify_params__(self):
    exists = True
    try:
      module = import_module(f'uploaders.{self.type}')
      return getattr(module, 'verify_params')(self.params)
    except ModuleNotFoundError:
      exists = False

    if not exists:
      raise UploaderError(f'unknown uploader "{self.type}"')

  def execute(self, filename: str):
    module = import_module(f'uploaders.{self.type}')
    getattr(module, 'upload_file')(self, filename)
