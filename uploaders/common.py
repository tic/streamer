class Uploader:
  type: str
  params: dict

  def __init__(self, type: str, params: dict):
    self.type = type
    self.params = params
