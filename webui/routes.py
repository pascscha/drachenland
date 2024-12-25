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
