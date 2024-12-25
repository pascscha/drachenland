from webui import webui
from marionette.pose import PoseEstimator

if __name__ == "__main__":
    with PoseEstimator() as pose_estimator:
        webui.pose_estimator = pose_estimator
        webui.run(host="0.0.0.0", port=5001)
