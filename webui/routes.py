import flask
import cv2
import json
import os
import sys
import math
import shutil
from datetime import datetime
from functools import wraps
from flask import request, Response, send_from_directory
from werkzeug.utils import secure_filename


def check_auth(username, password):
    # Replace these with your desired credentials
    return username == "mjrsch" and password == "Barsch Mond"


def authenticate():
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # auth = request.authorization
        # if not auth or not check_auth(auth.username, auth.password):
        #     return authenticate()
        return f(*args, **kwargs)

    return decorated


webui = flask.Flask(__name__)
ANIMATIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'animations', 'dances')


@webui.context_processor
def inject_globals():
    return dict(local_url=webui.config.get("LOCAL_URL"))


@webui.route("/")
@requires_auth
def index():
    return flask.render_template("dashboard.html")


@webui.route("/animation")
@requires_auth
def animation():
    with open(webui.config_path) as f:
        config = json.load(f)
    servos = sorted(list(config["gpio"]["servos"].values()), key=lambda x: x["name"])
    gpios = sorted(list(config["gpio"]["gpios"].values()), key=lambda x: x["name"])
    servo_half = math.ceil(len(servos) / 2)
    gpio_half = math.ceil(len(gpios) / 2)
    return flask.render_template(
        "animation.html",
        servos1=servos[:servo_half],
        servos2=servos[servo_half:],
        gpios1=gpios[:gpio_half],
        gpios2=gpios[gpio_half:],
    )


@webui.route("/animations", methods=["GET", "POST"])
@requires_auth
def manage_animations():
    if not os.path.exists(ANIMATIONS_PATH):
        os.makedirs(ANIMATIONS_PATH)

    if request.method == "POST":
        if "file" not in request.files:
            return flask.redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            return flask.redirect(request.url)
        if file and file.filename.endswith(".json"):
            filename = secure_filename(file.filename)
            file.save(os.path.join(ANIMATIONS_PATH, filename))
        return flask.redirect(flask.url_for("manage_animations"))

    animations = sorted([f for f in os.listdir(ANIMATIONS_PATH) if f.endswith(".json")])
    return flask.render_template("animations.html", animations=animations)


@webui.route("/animations/download/<filename>", methods=["GET"])
@requires_auth
def download_animation(filename):
    filename = secure_filename(filename)
    print(ANIMATIONS_PATH, filename)
    # Ensure the file is in the ANIMATIONS_PATH to prevent directory traversal
    return send_from_directory(ANIMATIONS_PATH, filename, as_attachment=True)


@webui.route("/animations/delete/<filename>", methods=["POST"])
@requires_auth
def delete_animation(filename):
    filename = secure_filename(filename)
    file_path = os.path.join(ANIMATIONS_PATH, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return flask.redirect(flask.url_for("manage_animations"))


@webui.route("/camera")
@requires_auth
def camera():
    return flask.render_template("camera.html")


@webui.route("/settings")
@requires_auth
def settings():
    return flask.render_template("settings.html")


@webui.route("/state")
@requires_auth
def state():  # Changed from settings() to state()
    return flask.render_template("state.html")


@webui.route("/get_state")
@requires_auth
def get_state():
    pose_estimator = webui.state_machine.context.pose_estimator
    dance_animations = webui.state_machine.context.animations["dances"]
    with open("animation-log-2025.log", "r") as f:
        timestamps = f.read().strip().split("\n")
    return flask.jsonify(
        {
            "state": webui.state_machine.state.value,
            "presence_time": pose_estimator.presence_time,
            "wave_time": pose_estimator.wave_time,
            "pose_x": pose_estimator.pose_x,
            "dance_index": dance_animations.index,
            "current_dance": dance_animations.animations[dance_animations.index].name,
            "n_started": len(timestamps),
        }
    )


@webui.route("/capture_image")
@requires_auth
def capture_image():
    frame = webui.pose_estimator.get_image()
    ret, buffer = cv2.imencode(".jpg", frame)
    frame_bytes = buffer.tobytes()
    return flask.Response(frame_bytes, mimetype="image/jpeg")


@webui.route("/gpio_config", methods=["GET", "POST"])
@requires_auth
def gpio_config():
    if request.method == "POST":
        if os.path.exists(webui.config_path):
            config_dir, config_filename = os.path.split(webui.config_path)
            name, ext = os.path.splitext(config_filename)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            backup_filename = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(config_dir, backup_filename)
            shutil.copy2(webui.config_path, backup_path)
        with open(webui.config_path, "r") as f:
            config = json.load(f)
        config["gpio"] = request.json
        with open(webui.config_path, "w") as f:
            json.dump(config, f, indent=4)
        return flask.jsonify({"message": "Configuration saved successfully."})
    else:
        with open(webui.config_path) as f:
            config = json.load(f)
        return flask.jsonify(config.get("gpio", {}))


@webui.route("/restart", methods=["POST"])
@requires_auth
def restart():
    # This is a simple way to restart. Note it might not handle all edge cases.
    try:
        # Give the client time to receive the response
        def do_restart():
            import time

            time.sleep(1)
            os.execv(sys.executable, ["python"] + sys.argv)

        from threading import Thread

        Thread(target=do_restart).start()
        return flask.jsonify({"message": "System is restarting..."})
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500


@webui.route("/marionette/set", methods=["POST"])
@requires_auth
def get_image():
    # Set servo to slider positions
    webui.marionette_animator.slider_values = {
        key: int(float(value)) for key, value in flask.request.form.items()
    }
    return flask.jsonify({"status": "ok"})


@webui.route("/marionette/play", methods=["POST"])
@requires_auth
def play():
    animation = flask.request.json.get("animation")
    webui.marionette_animator.start_animation(animation)
    return flask.jsonify({"status": "ok"})


@webui.route("/marionette/pause", methods=["POST"])
@requires_auth
def pause():
    webui.marionette_animator.stop_animation()
    return flask.jsonify({"status": "ok"})


@webui.route("/marionette/current_index", methods=["GET"])
@requires_auth
def current_index():
    current_frame = webui.marionette_animator.get_current_frame()
    return flask.jsonify({"current_index": current_frame})


@webui.route("/marionette/enabled", methods=["GET"])
@requires_auth
def get_enabled_status():
    return flask.jsonify({"enabled": webui.marionette_animator.target_strength == 1})


@webui.route("/marionette/enabled", methods=["POST"])
@requires_auth
def set_enabled_status():
    data = flask.request.json
    enabled = data.get("enabled", False)
    if enabled:
        webui.marionette_animator.animate_strength(1)
    else:
        webui.marionette_animator.animate_strength(0)
    return flask.jsonify({"status": "ok", "enabled": enabled})
