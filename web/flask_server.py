from threading import Timer
from flask import Flask, render_template, Response, session, redirect, request
from hashlib import sha256
from functools import wraps
from camera.camera import get_camera_instance
from config import config

def token(user, passwd):
  return sha256(str(user + passwd).encode()).hexdigest()

def format_frame(raw_frame):
  return (
    b'--frame\r\n'
    b'Content-Type: image/jpeg\r\n\r\n' + raw_frame + b'\r\n'
  )

web_config = config['web']
page_title = web_config['page_title']

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')
app.secret_key = web_config['secret']

"""Video streaming generator function."""
def StreamGenerator(cam_id):
  camera = get_camera_instance(cam_id)
  while True:
    raw_frame = camera.get_bytes_frame()
    yield format_frame(raw_frame)

def ImageGenerator(cam_id):
  camera = get_camera_instance(cam_id)
  camera.flush()
  return format_frame(camera.get_bytes_frame())

def require_login(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    try:
      if session['access_token'] == token(session['user'], web_config['logins'][session['user']]):
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
      if web_config['logins'][request.form['user']] == request.form['pass']:
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

"""Video streaming route. Put this in the src attribute of an img tag."""
@app.route(f'/feed/<camera_id>')
@require_login
def video_feed(camera_id):
  return Response(
    StreamGenerator(camera_id),
    mimetype='multipart/x-mixed-replace; boundary=frame'
  )

@app.route(f'/image/<camera_id>')
@require_login
def image_feed(camera_id):
  return Response(
    ImageGenerator(camera_id),
    mimetype='multipart/x-mixed-replace; boundary=frame'
  )

def run_app():
  if web_config['enabled']:
    Timer(0, lambda: app.run(host='0.0.0.0', port=web_config['port'], threaded=True)).start()
  else:
    print('[FLASK] web server disabled')
