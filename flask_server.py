from flask import Flask, render_template, Response, session, redirect, request, send_from_directory
from os.path import join as os_pathjoin
from hashlib import sha256
from functools import wraps
from time import sleep
from camera import get_camera_instance
from config import config

token = lambda usr, pas : sha256(str(usr + pas).encode()).hexdigest()

html_config = config['html']
page_title = html_config['page_title']

app = Flask(__name__)
app.secret_key = config['secret']

"""Video streaming generator function."""
def StreamGenerator(cam_id):
  camera = get_camera_instance(cam_id)
  while True:
    frame = camera.get_frame()
    yield (
      b'--frame\r\n'
      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
    )
    sleep(camera.delta)

def require_login(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    try:
      if session['access_token'] == token(session['user'], config['logins'][session['user']]):
        return f(*args, **kwargs)
    except KeyError:
      pass
    return redirect('/login')
  return decorated

"""Camera directory."""
@app.route('/')
@require_login
def index():
  cameras = [{ **config['cameras'][camera_id], 'id': camera_id } for camera_id in config['cameras']]
  return render_template(
    'index.html',
    cameras=cameras,
    page_title=page_title
  )

@app.route('/camera/<raw_camera_id>')
@require_login
def camera(raw_camera_id: str):
  try:
    camera_id = int(raw_camera_id)
    camera = { **config['cameras'][camera_id], 'id': camera_id }
    return render_template(
      'camera.html',
      camera=camera,
      page_title=page_title
    )
  except (KeyError, ValueError):
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    try:
      if config['logins'][request.form['user']] == request.form['pass']:
        # Login approved
        session['access_token'] = token(request.form['user'], request.form['pass'])
        session['user'] = request.form['user']
        return redirect('/')
    except KeyError:
      pass
  # Login denied, default back to original return
  return render_template('login.html')

@app.route('/logout')
def logout():
  try:
    session.pop('access_token', None)
    session.pop('user', None)
  except KeyError:
    pass
  return redirect('/login')

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os_pathjoin(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

"""Video streaming route. Put this in the src attribute of an img tag."""
for camera_id in config['cameras'].keys():
  @app.route(f'/feed/{camera_id}')
  @require_login
  def video_feed():
    return Response(
      StreamGenerator(camera_id),
      mimetype='multipart/x-mixed-replace; boundary=frame'
    )
