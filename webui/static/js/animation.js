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
    // Update sliders and their value displays
    for (const motor in values) {
        const slider = document.getElementById(motor);
        if (slider) {
            slider.value = values[motor];
            const valueDisplay = document.getElementById(`${motor}-value`);
            if (valueDisplay) {
                valueDisplay.textContent = `[${values[motor]}]`;
            }
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
        currentKeyframe[key] = parseInt(value);
    });

    // Check if a keyframe already exists at the current frame index
    const existingKeyframeIndex = keyframes.findIndex(keyframe => keyframe.frameIndex === currentFrameIndex);

    if (existingKeyframeIndex !== -1) {
        // Replace values of the existing keyframe
        keyframes[existingKeyframeIndex].values = currentKeyframe;
    } else {
        // Add new keyframe
        keyframes.push({ frameIndex: currentFrameIndex, values: currentKeyframe });

        // Sort the keyframes array by frameIndex
        keyframes.sort((a, b) => a.frameIndex - b.frameIndex);
    }

    drawTimeline();
    updateLocalStorage();
}


// Function to remove a keyframe at the current play position
function removeKeyframe() {

    for (let i = 0; i < selected["shift"].length; i++) {
        const indexToRemove = keyframes.findIndex(keyframe => keyframe.frameIndex === selected["shift"][i]);

        // If keyframe(s) found, remove them from the keyframes array
        if (indexToRemove !== -1) {
            keyframes.splice(indexToRemove, 1);
        }
    }

    if (selected["current"] !== null) {
        const indexToRemove = keyframes.findIndex(keyframe => keyframe.frameIndex === selected["current"]);

        // If keyframe(s) found, remove them from the keyframes array
        if (indexToRemove !== -1) {
            keyframes.splice(indexToRemove, 1);
        }

    }

    selected["shift"] = []
    selected["current"] = null;

    // Redraw the timeline canvas to reflect the changes
    drawTimeline();
    updateLocalStorage();
}


function previousFrame() {
    // Move backward one frame
    currentFrameIndex = Math.max(currentFrameIndex - 1, 0);
    markerX = (currentFrameIndex / totalFrames) * timelineWidth;
    updateShift();
    drawTimeline();
}

function nextFrame() {
    // Move forward one frame
    currentFrameIndex = Math.min(currentFrameIndex + 1, totalFrames - 1);
    markerX = (currentFrameIndex / totalFrames) * timelineWidth;
    updateShift();
    drawTimeline();
}


// Function to draw the timeline canvas
function drawTimeline() {
    timelineCtx.clearRect(0, 0, timelineCanvas.width, timelineCanvas.height);

    // Draw timeline background
    timelineCtx.fillStyle = "#333"; // Dark background color
    timelineCtx.fillRect(0, 0, timelineCanvas.width, timelineCanvas.height);

    // Draw keyframes
    keyframes.forEach(keyframe => {
        const xPos = (keyframe.frameIndex / totalFrames) * timelineWidth;
        if (keyframe.frameIndex == currentFrameIndex) {
            selected["current"] = keyframe.frameIndex;
            timelineCtx.fillStyle = "#f22"; // Red color for current keyframe
        } else if (selected["shift"].includes(keyframe.frameIndex)) {
            // console.log({ c: "red", i: keyframe.frameIndex })
            timelineCtx.fillStyle = "#f22"; // Red color for selected, non-current keyframes
        }
        else {
            timelineCtx.fillStyle = "#aaa"; // Gray color for unselected keyframes    
        }
        timelineCtx.beginPath();
        timelineCtx.arc(xPos, timelineCanvas.height / 2, 5, 0, Math.PI * 2);
        timelineCtx.fill();
    });


    // Update the marker position and redraw the timeline
    markerX = (currentFrameIndex / totalFrames) * timelineWidth;

    // Draw marker
    timelineCtx.fillStyle = "#0f0"; // Green color for marker
    timelineCtx.fillRect(markerX, 0, 2, timelineCanvas.height);

    drawPose();
}

function updateShift() {
    selected["shift"] = [];
    if (shiftPressed) {
        if (currentFrameIndex < shiftStartIndex) {
            startIndex = currentFrameIndex;
            endIndex = shiftStartIndex;
        }
        else {
            startIndex = shiftStartIndex;
            endIndex = currentFrameIndex;
        }

        console.log(startIndex)
        console.log(endIndex)
        selected["shift"] = [];
        for (let i = 0; i < keyframes.length; i++) {
            if (keyframes[i].frameIndex > endIndex) {
                break;
            }
            if (keyframes[i].frameIndex > startIndex) {
                selected["shift"].push(keyframes[i].frameIndex);
            }
        }
    }
}
// Function to handle click on the timeline canvas
function handleCanvasClick(event) {
    const rect = timelineCanvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;

    // Calculate the current frame index based on the click position
    currentFrameIndex = Math.floor((mouseX / (timelineWidth - 40)) * totalFrames);

    updateShift();
    drawTimeline();
}


// Function to copy the current keyframe data as JSON
function copyKeyframe() {
    let copyData = []

    let firstIndex = null;
    for (let i = 0; i < keyframes.length; i++) {
        if (selected["shift"].includes(keyframes[i].frameIndex) || keyframes[i].frameIndex == currentFrameIndex) {
            if (firstIndex === null) {
                firstIndex = keyframes[i].frameIndex;
            }
            let new_keyframe = { ...keyframes[i] };
            new_keyframe.frameIndex -= firstIndex;
            copyData.push(new_keyframe)
        }
    }

    localStorage.setItem("clipboard", JSON.stringify(copyData));
}

// Function to paste keyframe data from clipboard
function pasteKeyframe() {
    const text = localStorage.getItem("clipboard");

    try {
        var copyData = JSON.parse(text);
        let firstIndex = currentFrameIndex;

        for (let i = 0; i < copyData.length; i++) {
            const existingKeyframeIndex = keyframes.findIndex(keyframe => keyframe.frameIndex === firstIndex + copyData[i].frameIndex);

            if (existingKeyframeIndex !== -1) {
                // Replace values of the existing keyframe
                keyframes[existingKeyframeIndex].values = copyData[i].values;
            } else {
                // Add new keyframe
                keyframes.push({ frameIndex: firstIndex + copyData[i].frameIndex, values: copyData[i].values });

            }
        }

        // Sort the keyframes array by frameIndex
        keyframes.sort((a, b) => a.frameIndex - b.frameIndex);
        drawTimeline();
    } catch (error) {
        console.error("Error parsing clipboard data:", error);
    }

}

function undo() {
    historyIndex -= 1;
    if (historyIndex < 0) {
        historyIndex = 0;
    }

    console.log("undo", historyIndex)

    let data = { "history": history, "historyIndex": historyIndex }
    localStorage.setItem("data", JSON.stringify(data));
    loadLocalStoarge()
    drawTimeline()

}

function redo() {
    historyIndex += 1;
    if (historyIndex >= history.length) {
        historyIndex = history.length - 1;
    }

    let data = { "history": history, "historyIndex": historyIndex }
    localStorage.setItem("data", JSON.stringify(data));
    loadLocalStoarge()

}

// Function to handle keydown event for moving backward and forward one frame
function handleKeyDown(event) {
    if (event.key === "ArrowLeft") {
        previousFrame();
    } else if (event.key === "ArrowRight") {
        nextFrame();
    }
    else if (event.key === " ") { // Space key
        togglePlayPause();
    }
    else if (event.key === "Enter") {
        addKeyframe();
    }
    else if (event.key === "Delete") {
        removeKeyframe();
    }
    else if (event.ctrlKey && event.key === "c") {
        copyKeyframe();
    }
    else if (event.ctrlKey && event.key === "x") {
        copyKeyframe();
        removeKeyframe();
    }
    else if (event.ctrlKey && event.key === "v") {
        pasteKeyframe();
    }
    else if (event.ctrlKey && event.key === "z") {
        undo();
    }
    else if (event.ctrlKey && event.key === "y") {
        redo();
    }
    else if (event.key == "Shift") {
        shiftPressed = true;
        shiftStartIndex = currentFrameIndex;
    }
}

function handleKeyUp(event) {
    if (event.key == "Shift") {
        shiftPressed = false;
    }
}



// Event listener for keydown event
document.addEventListener("keydown", handleKeyDown);
document.addEventListener("keyup", handleKeyUp);

// Function to load keyframes from local storage
function loadFromLocalStorage() {
    const data = localStorage.getItem("data");
    if (data) {
        setData(JSON.parse(data));
    }
}


async function loadLocalStoarge() {
    // Call loadKeyframesFromLocalStorage when initializing the application
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const loadParam = urlParams.get('load');
    if (loadParam) {
        // If load parameter exists, try to load from remote URL
        try {
            const response = await fetch(`/static/animations/${loadParam}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const keyframesData = await response.json();
            console.log({
                history: [keyframesData],
                historyIndex: 0
            })
            setData({
                history: [keyframesData],
                historyIndex: 0
            });

            drawTimeline();
            updateLocalStorage();

        } catch (error) {
            console.error('Error loading keyframes from URL:', error);
            // Fallback to local storage if remote loading fails
            loadFromLocalStorage();
            drawTimeline();
            updateLocalStorage();

        }
    } else {
        // If no load parameter, load from local storage
        loadFromLocalStorage();
        drawTimeline();
        updateLocalStorage();
    }
}

loadLocalStoarge();

// Function to toggle between play and pause states
function togglePlayPause() {
    const playPauseBtn = document.getElementById("playPauseBtn");
    if (isPlaying) {
        stopAnimation();
        playPauseBtn.innerHTML = "&#9205;"; // Unicode for play symbol
    } else {
        startAnimation();
        playPauseBtn.innerHTML = "&#9208;"; // Unicode for pause symbol
    }
}

// Event listener for play/pause button
document.getElementById("playPauseBtn").addEventListener("click", togglePlayPause);

// Event listeners for keyframe controls
document.getElementById("addKeyframeBtn").addEventListener("click", addKeyframe);
document.getElementById("removeKeyframeBtn").addEventListener("click", removeKeyframe);

document.getElementById("previousFrameBtn").addEventListener("click", previousFrame);
document.getElementById("nextFrameBtn").addEventListener("click", nextFrame);

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

// document.getElementById("undoBtn").addEventListener("click", function () {
//     undo();
// });

// document.getElementById("redoBtn").addEventListener("click", function () {
//     redo();
// });


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

// EXPORT IMPORT
// Function to export keyframes
// Function to export keyframes including totalFrames and fps
function exportKeyframes() {
    const keyframesJson = JSON.stringify(getConfig(), null, 2);
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
        const enabled = this.checked;
        fetch('/marionette/enabled', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled: enabled })
        })
    });

    // Add event listeners for sliders to show current value
    const sliders = document.querySelectorAll('#sliderForm input[type="range"]');
    sliders.forEach(slider => {
        const valueSpan = document.getElementById(`${slider.id}-value`);
        if (valueSpan) {
            // Set initial value from slider's default
            valueSpan.textContent = `[${slider.value}]`;
            // Add listener to update on change
            slider.addEventListener('input', event => {
                valueSpan.textContent = `[${event.target.value}]`;
            });
        }
    });
});

// Initial draw of the timeline
drawTimeline();