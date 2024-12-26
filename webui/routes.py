import flask
import cv2

webui = flask.Flask(__name__)


@webui.route("/")
def index():
    return flask.render_template("dashboard.html")


@webui.route("/animation")
def animation():
    return flask.render_template("animation.html")


@webui.route("/camera")
def camera():
    return flask.render_template("camera.html")


@webui.route("/settings")
def settings():
    return flask.render_template("settings.html")


@webui.route("/state")
def state():  # Changed from settings() to state()
    return flask.render_template("state.html")


@webui.route("/get_state")
def get_state():
    pose_estimator = webui.state_machine.context.pose_estimator
    dance_animations = webui.state_machine.context.animations["dances"]

    return flask.jsonify(
        {
            "state": webui.state_machine.state.value,
            "presence_time": pose_estimator.presence_time,
            "wave_time": pose_estimator.wave_time,
            "pose_x": pose_estimator.pose_x,
            "dance_index": dance_animations.index,
            "current_dance": dance_animations.animations[dance_animations.index].name,
        }
    )


@webui.route("/capture_image")
def capture_image():
    frame = webui.pose_estimator.get_image()

    ret, buffer = cv2.imencode(".jpg", frame)
    frame_bytes = buffer.tobytes()
    return flask.Response(frame_bytes, mimetype="image/jpeg")


@webui.route("/marionette/set", methods=["POST"])
def get_image():
    # Set servo to slider positions
    webui.marionette_animator.slider_values = {
        key: int(value) for key, value in flask.request.form.items()
    }
    return flask.jsonify({"status": "ok"})


@webui.route("/marionette/play", methods=["POST"])
def play():
    animation = flask.request.json.get("animation")
    webui.marionette_animator.start_animation(animation)
    return flask.jsonify({"status": "ok"})


@webui.route("/marionette/pause", methods=["POST"])
def pause():
    webui.marionette_animator.stop_animation()
    return flask.jsonify({"status": "ok"})


@webui.route("/marionette/current_index", methods=["GET"])
def current_index():
    current_frame = webui.marionette_animator.get_current_frame()
    return flask.jsonify({"current_index": current_frame})


@webui.route("/marionette/enabled", methods=["GET"])
def get_enabled_status():
    return flask.jsonify({"enabled": webui.marionette_animator.target_strength == 1})


@webui.route("/marionette/enabled", methods=["POST"])
def set_enabled_status():
    data = flask.request.json
    enabled = data.get("enabled", False)
    if enabled:
        webui.marionette_animator.animate_strength(1)
    else:
        webui.marionette_animator.animate_strength(0)
    return flask.jsonify({"status": "ok", "enabled": enabled})
