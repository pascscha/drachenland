// Define variables to hold animation state
let isPlaying = false;
let animationInterval = null;
let currentFrameIndex = 0;
let keyframes = [];
let timelineCanvas = null;
let timelineCtx = null;
let timelineWidth = 0;
let markerX = 0;
let totalFrames = 100;
let fps = 10;
let shiftPressed = false;
let shiftStartIndex = null;
let selected = { "current": null, "shift": [] }
let history = []
let historyIndex = null;
// Function to start the animation
async function startAnimation() {
    if (!isPlaying) {
        isPlaying = true;
        const animationConfig = getConfig();
        try {
            const response = await fetch('/marionette/play', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ animation: animationConfig }),
            });
            if (!response.ok) {
                throw new Error('Failed to start animation');
            }
            animationInterval = setInterval(animate, 250); // Adjust interval as needed
        } catch (error) {
            console.error('Error starting animation:', error);
        }
    }
}
// Function to stop the animation
async function stopAnimation() {
    if (isPlaying) {
        isPlaying = false;
        clearInterval(animationInterval);
        try {
            const response = await fetch('/marionette/pause', {
                method: 'POST',
            });
            if (!response.ok) {
                throw new Error('Failed to stop animation');
            }
        } catch (error) {
            console.error('Error stopping animation:', error);
        }
    }
}
// Function to animate between keyframes
async function animate() {
    try {
        const response = await fetch('/marionette/current_index');
        if (!response.ok) {
            throw new Error('Failed to fetch current index');
        }
        const data = await response.json();
        currentFrameIndex = data.current_index;
        // Calculate the position of the green marker
        markerX = (currentFrameIndex / totalFrames) * timelineWidth;
        // Redraw the timeline canvas with the updated marker position
        drawTimeline();
    } catch (error) {
        console.error('Error fetching current index:', error);
    }
}
function drawPose() {
    // Find keyframe before and keyframe after
    let keyframeBefore = null;
    let keyframeAfter = null;
    for (let i = 0; i < keyframes.length; i++) {
        if (keyframes[i].frameIndex <= currentFrameIndex) {
            keyframeBefore = keyframes[i];
        } else {
            keyframeAfter = keyframes[i];
            break;
        }
    }
    // If there are no keyframes, do nothing
    if (!keyframeBefore && !keyframeAfter) {
        return;
    }
    // If there is no keyframe before, use the position of the first keyframe
    if (!keyframeBefore) {
        updateSlidersAndDraw(keyframeAfter.values);
        return;
    }
    // If there is no keyframe after, use the position of the last keyframe
    if (!keyframeAfter) {
        keyframeAfter = {
            "frameIndex": totalFrames + 1,
            "values": keyframes[0].values
        }
    }
    // Interpolate motor positions between keyframes
    const progress = (currentFrameIndex - keyframeBefore.frameIndex) / (keyframeAfter.frameIndex - keyframeBefore.frameIndex);
    const interpolatedValues = {};
    for (const motor in keyframeBefore.values) {
        const startValue = keyframeBefore.values[motor];
        const endValue = keyframeAfter.values[motor];
        interpolatedValues[motor] = Math.round(startValue + (endValue - startValue) * progress);
    }
    updateSlidersAndDraw(interpolatedValues);
}
// Function to update sliders and draw timeline
function updateSlidersAndDraw(values) {
    console.log(values)
    // Update sliders
    for (const motor in values) {
        const slider = document.getElementById(motor);
        if (slider) {
            slider.value = values[motor];
        }
    }
    // Redraw the timeline canvas with the updated marker position
    markerX = (currentFrameIndex / totalFrames) * timelineWidth;
    handleSliderChange();
}
// Function to update local storage with keyframes data
function updateLocalStorage() {
    let config = getConfig();
    if (historyIndex !== null && historyIndex !== history.length - 1) {
        history = history.slice(0, historyIndex + 1);
    }
    history.push(JSON.parse(JSON.stringify(config)));
    historyIndex = history.length - 1;
    let data = { "history": history, "historyIndex": historyIndex };
    localStorage.setItem("data", JSON.stringify(data));
}
// Function to add or update a keyframe at the current play position
function addKeyframe() {
    // Get current slider values
    const sliderForm = document.getElementById("sliderForm");
    const formData = new FormData(sliderForm);
    const currentKeyframe = {};
    formData.forEach((value, key) => {
        currentKeyframe[key] = value;
    });
    // Find if a keyframe already exists at the current frame index
    const existingKeyframeIndex = keyframes.findIndex(
        (kf) => kf.frameIndex === currentFrameIndex
    );
    if (existingKeyframeIndex !== -1) {
        // Update existing keyframe
        keyframes[existingKeyframeIndex].values = currentKeyframe;
    } else {
        // Add new keyframe
        keyframes.push({
            frameIndex: currentFrameIndex,
            values: currentKeyframe,
        });
        // Sort keyframes by frame index
        keyframes.sort((a, b) => a.frameIndex - b.frameIndex);
    }
    // Redraw the timeline
    drawTimeline();
    updateLocalStorage();
}
// Function to remove a keyframe at the current play position
function removeKeyframe() {
    // Find if a keyframe exists at the current frame index
    const existingKeyframeIndex = keyframes.findIndex(
        (kf) => kf.frameIndex === currentFrameIndex
    );
    if (existingKeyframeIndex !== -1) {
        // Remove the keyframe
        keyframes.splice(existingKeyframeIndex, 1);
        // Redraw the timeline
        drawTimeline();
        updateLocalStorage();
    }
}
function copyKeyframe() {
    const existingKeyframe = keyframes.find(
        (kf) => kf.frameIndex === currentFrameIndex
    );
    if (existingKeyframe) {
        navigator.clipboard.writeText(JSON.stringify(existingKeyframe.values, null, 2));
    }
}
function pasteKeyframe() {
    navigator.clipboard.readText().then(clipText => {
        let values = JSON.parse(clipText)
        const existingKeyframeIndex = keyframes.findIndex(
            (kf) => kf.frameIndex === currentFrameIndex
        );
        if (existingKeyframeIndex !== -1) {
            keyframes[existingKeyframeIndex].values = values;
        } else {
            keyframes.push({
                frameIndex: currentFrameIndex,
                values: values,
            });
            keyframes.sort((a, b) => a.frameIndex - b.frameIndex);
        }
        drawTimeline();
        updateLocalStorage();
    }).catch(err => {
        console.error('Failed to read clipboard contents: ', err);
    });
}
function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        setData({ "history": history, "historyIndex": historyIndex })
        localStorage.setItem("data", JSON.stringify({ "history": history, "historyIndex": historyIndex }));
    }
}
function redo() {
    if (historyIndex < history.length - 1) {
        historyIndex++;
        setData({ "history": history, "historyIndex": historyIndex })
        localStorage.setItem("data", JSON.stringify({ "history": history, "historyIndex": historyIndex }));
    }
}
// Load data from local storage on page load
document.addEventListener("DOMContentLoaded", function () {
    let data = localStorage.getItem("data");
    if (!data) {
        history = [getConfig()]
        historyIndex = 0;
        data = { "history": history, "historyIndex": historyIndex }
        localStorage.setItem("data", JSON.stringify(data));
    }
    setData(JSON.parse(data));
    const totalFramesInput = document.getElementById("totalFrames");
    const fpsInput = document.getElementById("fps");
    totalFramesInput.value = totalFrames;
    fpsInput.value = fps;
});
document.addEventListener('keydown', (event) => {
    shiftPressed = event.shiftKey;
    switch (event.code) {
        case "Space":
            event.preventDefault();
            playPause();
            break;
        case "ArrowRight":
            event.preventDefault();
            nextFrame();
            break;
            alue, key) => {
    currentKeyframe[key] = value;
});
// Find if a keyframe already exists at the current frame index
const existingKeyframeIndex = keyframes.findIndex(
    (kf) => kf.frameIndex === currentFrameIndex
);
if (existingKeyframeIndex !== -1) {
    // Update existing keyframe
    keyframes[existingKeyframeIndex].values = currentKeyframe;
} else {
    // Add new keyframe
    keyframes.push({
        frameIndex: currentFrameIndex,
        values: currentKeyframe,
    });
    // Sort keyframes by frame index
    keyframes.sort((a, b) => a.frameIndex - b.frameIndex);
}
// Redraw the timeline
drawTimeline();
updateLocalStorage();
}
// Function to remove a keyframe at the current play position
function removeKeyframe() {
    // Find if a keyframe exists at the current frame index
    const existingKeyframeIndex = keyframes.findIndex(
        (kf) => kf.frameIndex === currentFrameIndex
    );
    if (existingKeyframeIndex !== -1) {
        // Remove the keyframe
        keyframes.splice(existingKeyframeIndex, 1);
        // Redraw the timeline
        drawTimeline();
        updateLocalStorage();
    }
}
function copyKeyframe() {
    const existingKeyframe = keyframes.find(
        (kf) => kf.frameIndex === currentFrameIndex
    );
    if (existingKeyframe) {
        navigator.clipboard.writeText(JSON.stringify(existingKeyframe.values, null, 2));
    }
}
function pasteKeyframe() {
    navigator.clipboard.readText().then(clipText => {
        let values = JSON.parse(clipText)
        const existingKeyframeIndex = keyframes.findIndex(
            (kf) => kf.frameIndex === currentFrameIndex
        );
        if (existingKeyframeIndex !== -1) {
            keyframes[existingKeyframeIndex].values = values;
        } else {
            keyframes.push({
                frameIndex: currentFrameIndex,
                values: values,
            });
            keyframes.sort((a, b) => a.frameIndex - b.frameIndex);
        }
        drawTimeline();
        updateLocalStorage();
    }).catch(err => {
        console.error('Failed to read clipboard contents: ', err);
    });
}
function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        setData({ "history": history, "historyIndex": historyIndex })
        localStorage.setItem("data", JSON.stringify({ "history": history, "historyIndex": historyIndex }));
    }
}
function redo() {
    if (historyIndex < history.length - 1) {
        historyIndex++;
        setData({ "history": history, "historyIndex": historyIndex })
        localStorage.setItem("data", JSON.stringify({ "history": history, "historyIndex": historyIndex }));
    }
}
// Load data from local storage on page load
document.addEventListener("DOMContentLoaded", function () {
    let data = localStorage.getItem("data");
    if (!data) {
        history = [getConfig()]
        historyIndex = 0;
        data = { "history": history, "historyIndex": historyIndex }
        localStorage.setItem("data", JSON.stringify(data));
    }
    setData(JSON.parse(data));
    const totalFramesInput = document.getElementById("totalFrames");
    const fpsInput = document.getElementById("fps");
    totalFramesInput.value = totalFrames;
    fpsInput.value = fps;
});
document.addEventListener('keydown', (event) => {
    shiftPressed = event.shiftKey;
    switch (event.code) {
        case "Space":
            event.preventDefault();
            playPause();
            break;
        case "ArrowRight":
            event.preventDefault();
            nextFrame();
            break;
        case "ArrowLeft":
            event.preventDefault();
            previousFrame();
            break;
        case "KeyC":
            if (event.ctrlKey) {
                event.preventDefault();
                copyKeyframe();
            }
            break;
        case "KeyV":
            if (event.ctrlKey) {
                event.preventDefault();
                pasteKeyframe();
            }
            break;
        case "KeyX":
            if (event.ctrlKey) {
                event.preventDefault();
                copyKeyframe();
                removeKeyframe();
            }
            break;
        case "KeyZ":
            if (event.ctrlKey) {
                event.preventDefault();
                undo();
            }
            break;
        case "KeyY":
            if (event.ctrlKey) {
                event.preventDefault();
                redo();
            }
            break;
    }
});
document.addEventListener('keyup', (event) => {
    shiftPressed = event.shiftKey;
});
// Function to play/pause the animation
function playPause() {
    const playPauseBtn = document.getElementById("playPauseBtn");
    if (isPlaying) {
        stopAnimation();
        playPauseBtn.innerHTML = "▶"; // Play symbol
    } else {
        startAnimation();
        playPauseBtn.innerHTML = "❚❚"; // Pause symbol
    }
}
// Function to move to the next frame
function nextFrame() {
    currentFrameIndex = (currentFrameIndex + 1);
    if (currentFrameIndex >= totalFrames) {
        currentFrameIndex = 0;
    }
    updateLocalStorage();
    drawPose();
    drawTimeline();
}
// Function to move to the previous frame
function previousFrame() {
    currentFrameIndex = (currentFrameIndex - 1);
    if (currentFrameIndex < 0) {
        currentFrameIndex = totalFrames - 1;
    }
    updateLocalStorage();
    drawPose();
    drawTimeline();
}
// Function to handle canvas click
function handleCanvasClick(event) {
    const rect = timelineCanvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    currentFrameIndex = Math.round((clickX / timelineWidth) * totalFrames);
    markerX = (currentFrameIndex / totalFrames) * timelineWidth;
    updateLocalStorage();
    drawTimeline();
    drawPose();
}
// Function to draw the timeline
function drawTimeline() {
    timelineCtx.clearRect(0, 0, timelineWidth, 100);
    // Draw the main timeline bar
    timelineCtx.fillStyle = "#ccc";
    timelineCtx.fillRect(0, 40, timelineWidth, 20);
    // Draw keyframe markers
    keyframes.forEach((kf) => {
        const x = (kf.frameIndex / totalFrames) * timelineWidth;
        timelineCtx.fillStyle = "blue";
        timelineCtx.beginPath();
        timelineCtx.moveTo(x, 30);
        timelineCtx.lineTo(x - 5, 20);
        timelineCtx.lineTo(x + 5, 20);
        timelineCtx.closePath();
        timelineCtx.fill();
    });
    // Draw the playhead (green marker)
    timelineCtx.fillStyle = "green";
    timelineCtx.fillRect(markerX - 2, 0, 4, 100);
}
// Add event listeners to buttons
document.getElementById("playPauseBtn").addEventListener("click", playPause);
document
    .getElementById("addKeyframeBtn")
    .addEventListener("click", addKeyframe);
document
    .getElementById("removeKeyframeBtn")
    .addEventListener("click", removeKeyframe);
document.getElementById("nextFrameBtn").addEventListener("click", nextFrame);
document
    .getElementById("previousFrameBtn")
    .addEventListener("click", previousFrame);
document.getElementById("copyBtn").addEventListener("click", function () {
    copyKeyframe();
});
document.getElementById("cutBtn").addEventListener("click", function () {
    copyKeyframe();
    removeKeyframe();
});
document.getElementById("pasteBtn").addEventListener("click", function () {
    pasteKeyframe();
});
// Initialize timeline canvas
timelineCanvas = document.getElementById("timelineCanvas");
timelineCtx = timelineCanvas.getContext("2d");
timelineWidth = timelineCanvas.width;
// Add event listener for canvas click
timelineCanvas.addEventListener("click", handleCanvasClick);
function getConfig() {
    return {
        keyframes: keyframes,
        config: {
            totalFrames: totalFrames,
            fps: fps,
            currentFrameIndex: currentFrameIndex
        }
    };
}
function setData(data) {
    if (!("history" in data) || !("historyIndex" in data)) {
        console.error("Missing 'history' or 'historyIndex' in data.");
        return;
    }
    history = data["history"];
    historyIndex = data["historyIndex"];
    if (historyIndex < 0 || historyIndex >= history.length) {
        console.error("Invalid 'historyIndex' value.");
        return;
    }
    let config = history[historyIndex];
    if (!config) {
        console.error("No config found at the specified 'historyIndex'.");
        return;
    }
    keyframes = config.keyframes;
    totalFrames = config.config.totalFrames;
    fps = config.config.fps;
    currentFrameIndex = config.config.currentFrameIndex;
    markerX = (currentFrameIndex / totalFrames) * timelineWidth;
}
// Function to export keyframes including totalFrames and fps
async function exportKeyframes() {
    let animationConfig = getConfig();
    try {
        const response = await fetch('/gpio_config');
        if (!response.ok) {
            throw new Error('Failed to fetch GPIO config');
        }
        animationConfig.gpioConfig = await response.json();
    } catch (error) {
        console.error('Error fetching GPIO config:', error);
        alert('Could not fetch GPIO config. It will not be included in the export.');
    }

    const keyframesJson = JSON.stringify(animationConfig, null, 2);
    const blob = new Blob([keyframesJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "keyframes.json";
    a.click();
    URL.revokeObjectURL(url);
}
// Function to handle import of keyframes
function importKeyframes(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        const keyframesData = JSON.parse(e.target.result);
        keyframes = keyframesData.keyframes;
        totalFrames = keyframesData.config.totalFrames;
        fps = keyframesData.config.fps;
        drawTimeline();
        updateLocalStorage();
    };
    reader.readAsText(file);
}
// Event listener for export button
document.getElementById("exportBtn").addEventListener("click", exportKeyframes);
// Event listener for import input
document.getElementById("importInput").addEventListener("change", importKeyframes);
// Get the Apply button
const applyBtn = document.getElementById("applyBtn");
// When the Apply button is clicked, apply the changes to totalFrames and fps
applyBtn.addEventListener("click", function () {
    const totalFramesInput = document.getElementById("totalFrames");
    const fpsInput = document.getElementById("fps");
    // Get the new values from the inputs
    const newTotalFrames = parseInt(totalFramesInput.value);
    const newFps = parseInt(fpsInput.value);
    // Update the global variables
    totalFrames = newTotalFrames;
    fps = newFps;
    updateLocalStorage()
    // Update any other related functionality or UI elements as needed
    drawTimeline()
});
// Get the modal
var modal = document.getElementById("settingsModal");
// Get the button that opens the modal
var btn = document.getElementById("settingsBtn");
// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];
// When the user clicks on the button, open the modal
btn.onclick = function () {
    modal.style.display = "block";
}
// When the user clicks on <span> (x), close the modal
span.onclick = function () {
    modal.style.display = "none";
}
// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('enableToggle');
    // Check initial state
    fetch('/marionette/enabled')
        .then(response => response.json())
        .then(data => {
            toggleButton.checked = data.enabled;
        });
    toggleButton.addEventListener('change', function () {
        const enabled = this.checked; _
        fetch('/marionette/enabled', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled: enabled })
        })
    });
});
// Initial draw of the timeline
drawTimeline();