from flask import Flask, render_template, Response
import cv2

webui = Flask(__name__)

@webui.route("/")
def index():
    return render_template("dashboard.html")

@webui.route("/animation")
def animation():
    return render_template("animation.html")

@webui.route("/camera")
def camera():
    return render_template("camera.html")

@webui.route("/settings")
def settings():
    return render_template("settings.html")

@webui.route('/capture_image')
def capture_image():
    frame = webui.pose_estimator.get_image()

    ret, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    return Response(frame_bytes, mimetype='image/jpeg')