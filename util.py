from datetime import datetime

timestamp = lambda : int(datetime.now().timestamp() * 1000)
class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKCYAN = '\033[96m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'

def log_message(message: str):
  try:
    with open(f'logs/{datetime.strftime(datetime.now(), "%Y.%m")}.streamer.log', 'a') as fp:
      fp.write(message)
  except:
    # Can't do a regular print statement because that could create a cyclical failure.
    pass

def time_string():
  return datetime.strftime(datetime.now(), '%Y.%m.%d-%H:%M:%S')
