import flask
import cv2

from functools import wraps
from flask import request, Response


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


@webui.route("/")
@requires_auth
def index():
    return flask.render_template("dashboard.html")


@webui.route("/animation")
@requires_auth
def animation():
    return flask.render_template("animation.html")


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

    with open("animation-log.log", "r") as f:
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


@webui.route("/marionette/set", methods=["POST"])
@requires_auth
def get_image():
    # Set servo to slider positions
    webui.marionette_animator.slider_values = {
        key: int(value) for key, value in flask.request.form.items()
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
