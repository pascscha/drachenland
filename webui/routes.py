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
from utils.time_utils import is_store_open, get_default_schedule


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

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ANIMATIONS_OPEN_PATH = os.path.join(BASE_DIR, "animations", "dances_open")
ANIMATIONS_CLOSED_PATH = os.path.join(BASE_DIR, "animations", "dances_closed")


def get_animation_path(category):
    if category == "open":
        return ANIMATIONS_OPEN_PATH
    elif category == "closed":
        return ANIMATIONS_CLOSED_PATH
    return ValueError("Invalid category")


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
    # Ensure directories exist
    for path in [ANIMATIONS_OPEN_PATH, ANIMATIONS_CLOSED_PATH]:
        if not os.path.exists(path):
            os.makedirs(path)

    if request.method == "POST":
        if "file" not in request.files:
            return flask.redirect(request.url)
        file = request.files["file"]
        category = request.form.get("category", "closed")

        target_path = get_animation_path(category)

        if file.filename == "":
            return flask.redirect(request.url)
        if file and file.filename.endswith(".json"):
            filename = secure_filename(file.filename)
            file.save(os.path.join(target_path, filename))
        return flask.redirect(flask.url_for("manage_animations"))

    animations_open = sorted(
        [f for f in os.listdir(ANIMATIONS_OPEN_PATH) if f.endswith(".json")]
    )
    animations_closed = sorted(
        [f for f in os.listdir(ANIMATIONS_CLOSED_PATH) if f.endswith(".json")]
    )

    return flask.render_template(
        "animations.html",
        animations_open=animations_open,
        animations_closed=animations_closed,
    )


@webui.route("/animations/download/<category>/<filename>", methods=["GET"])
@requires_auth
def download_animation(category, filename):
    filename = secure_filename(filename)
    target_path = get_animation_path(category)
    return send_from_directory(target_path, filename, as_attachment=True)


@webui.route("/animations/delete/<category>/<filename>", methods=["POST"])
@requires_auth
def delete_animation(category, filename):
    filename = secure_filename(filename)
    target_path = get_animation_path(category)
    file_path = os.path.join(target_path, filename)
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

    schedule = webui.state_machine.context.config.get(
        "opening_hours", get_default_schedule()
    )
    is_open = is_store_open(schedule)

    target_anim_key = "dances_open" if is_open else "dances_closed"
    dance_animations = webui.state_machine.context.animations.get(target_anim_key)

    with open("animation-log-2026.log", "r") as f:
        timestamps = f.read().strip().split("\n")

    response = {
        "state": webui.state_machine.state.value,
        "is_open": "Open" if is_open else "Closed",
        "presence_time": pose_estimator.presence_time,
        "wave_time": pose_estimator.wave_time,
        "pose_x": pose_estimator.pose_x,
        "n_started": len(timestamps),
    }

    if dance_animations:
        response["dance_index"] = dance_animations.index
        # Check index bounds
        if 0 <= dance_animations.index < len(dance_animations.animations):
            response["current_dance"] = dance_animations.animations[
                dance_animations.index
            ].name
        else:
            response["current_dance"] = "Index out of bounds"
    else:
        response["dance_index"] = "N/A"
        response["current_dance"] = "No animation set found"

    return flask.jsonify(response)


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


@webui.route("/config/schedule", methods=["GET", "POST"])
@requires_auth
def config_schedule():
    if request.method == "POST":
        with open(webui.config_path, "r") as f:
            config = json.load(f)

        config["opening_hours"] = request.json

        with open(webui.config_path, "w") as f:
            json.dump(config, f, indent=4)
        return flask.jsonify({"message": "Schedule saved successfully."})
    else:
        with open(webui.config_path) as f:
            config = json.load(f)

        from utils.time_utils import get_default_schedule

        return flask.jsonify(config.get("opening_hours", get_default_schedule()))


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
