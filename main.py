#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, session, redirect, request, send_from_directory
import cv2
from PIL import Image
import numpy as np
import io
from time import time
from datetime import datetime
import threading
import credentials
from hashlib import sha256
from functools import wraps
import subprocess
import re

# Quick function to generate a browser auth token
# Yeah, it's vulnerable to a ton of stuff. So?
token = lambda usr, pas : sha256(str(usr + pas).encode()).hexdigest()

# For small systems, like RaspberryPi, you may want to
# keep track of the CPU temperature via an on-screen HUD
track_cpu_temp = False

# Define cameras and their parameters
# Rotation options:
# - None
# - cv2.cv2.ROTATE_90_CLOCKWISE
# - cv2.cv2.ROTATE_180
# - cv2.cv2.ROTATE_90_COUNTERCLOCKWISE
Cameras = {
    0: {
        'fps': 30,
        'resolution': (854, 480),
        'mode': cv2.COLOR_BGR2RGB,
        'rotation': None
    }
}

# Capture CPU temp on a self-contained loop
cpu_temp_value = 'CPU Temp Unavailable (loading)'
def cpu_temp_loop():
    global cpu_temp_value
    try:
        output = subprocess.check_output(['vcgencmd', 'measure_temp'])
        output = output.decode('utf-8')
        val = re.search('temp=(\d+.\d+).*', output).group(1)
        cpu_temp_value = 'CPU Temp: ' + val #+ u'\N{DEGREE SIGN}' + 'C'
    except Exception as err:
        print(err)
        cpu_temp_value = 'CPU Temp Unavailable'
    finally:
        threading.Timer(10.0, cpu_temp_loop).start()
if track_cpu_temp: cpu_temp_loop()

# Camera class - represents a single physical camera.
class Camera:
    def __init__(self, cam_id):
        global Cameras
        self.vc = cv2.VideoCapture(cam_id)
        self.delta = 1.0 / Cameras[cam_id]['fps']
        self.res = Cameras[cam_id]['resolution']
        self.mode = Cameras[cam_id]['mode']
        self.rotation = Cameras[cam_id]['rotation']
        self.last_frame = 0
        self.saved_frame = None
        self.mutex = threading.Lock()

    def get_frame(self):
        try:
            with self.mutex:
                ctime = time()
                if (ctime - self.last_frame > self.delta) or self.saved_frame is None:
                    # If more than 1 frame's worth of time has elapsed,
                    # get a new frame.
                    if not self.vc.isOpened():
                        raise Exception("video stream closed unexpectedly")
                    rval, frame = self.vc.read()
                    if not rval:
                        raise Exception("frame read failed")

                    last_frame = ctime
                    frame = cv2.resize(frame, self.res, interpolation=cv2.INTER_AREA)
                    if self.mode is not None:
                        frame = cv2.cvtColor(frame, self.mode)

                    if self.rotation is not None:
                        frame = cv2.rotate(frame, self.rotation)

                    frame = cv2.putText(
                        frame, datetime.now().strftime('%D %H:%M:%S'),
                        (0, 18), cv2.FONT_HERSHEY_SIMPLEX,
                        0.60, (0, 255, 0), 1, cv2.LINE_AA
                    )

                    if track_cpu_temp:
                        frame = cv2.putText(
                            frame, cpu_temp_value,
                            (0, 38), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 255, 0), 1, cv2.LINE_AA
                        )

                    frame = Image.fromarray(frame, "RGB")
                    buf = io.BytesIO()
                    frame.save(buf, format='JPEG')
                    self.saved_frame = buf.getvalue()
        except Exception as err:
            print('[{}] frame update failed: {}'.format(ctime.strftime('%H:%M:%S'), err))
        finally:
            return self.saved_frame
#

# CameraManager class is used to wrap app Camera
# instances and ensure duplicates aren't created.
class CameraManager:
    def __init__(self):
        self.cams = {}

    def get_camera_instance(self, cam_id):
        try:
            cam_instance = self.cams[cam_id]
        except KeyError:
            cam_instance = Camera(cam_id)
            self.cams[cam_id] = cam_instance
        return cam_instance
#

# Initialize the camera manager
cam_man = CameraManager()

"""Video streaming generator function."""
# Creates a generator which yields a camera feed frame-by-frame
def StreamGenerator(cam_id):
    global cam_man

    # Get the instance of the desired camera
    camera = cam_man.get_camera_instance(cam_id)

    # Until the request is terminated, pull
    # new frames and propogate them upwards
    while True:
        frame = camera.get_frame()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )


# ############################ #
# ####### Flask Server ####### #
# ############################ #

# Create the flask server using the stored secret
app = Flask(__name__)
app.secret_key = credentials.secret;

# Decorator which checks for login token before permitting access
def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Look for a token in the session and see if it is a valid
        # token for the user they claim to be logged in as.
        try:
            if session['access_token'] == token(session['user'], credentials.logins[session['user']]):
                return f(*args, **kwargs)
        except KeyError:
            pass
        return redirect('/login')
        # ^^ Redirect them to the login page if there is no valid token present.
    return decorated

"""Video streaming home page."""
@app.route('/')
@require_login
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            if credentials.logins[request.form['user']] == request.form['pass']:
                # login approved
                session['access_token'] = token(request.form['user'], request.form['pass'])
                session['user'] = request.form['user']
                return redirect('/')
        except KeyError:
            pass
    # login denied, default back to original return
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
@app.route('/feed/0')
@require_login
def video_feed():
    return Response(
        StreamGenerator(0),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# Serve the favicon :)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Spin up the flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=42069, threaded=True)
