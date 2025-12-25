[**🇬🇧 English**](README.md) | [🇨🇭 Deutsch](README-DE.md)

# Drachenland Diorama 2025
![Python](https://img.shields.io/badge/python-3.11-blue.svg) ![License](https://img.shields.io/github/license/pascscha/drachenland)

![Diorama in Action](docs/images/wave.gif)

## 🐲 About the Project
This project controls an interactive diorama featuring a central **Dragon King** puppet and surrounding dragon and serpent figures. Unlike previous years, this installation is a full **diorama** showcasing various **carnival preparation steps** in a lively, animated scene.

The exhibit will be displayed from **January to beginning of March 2025** at:

> [**Goldschmied Armin Limacher**](https://goldschmied-limacher.ch/kontakt/)
>
> [Pilatusstrasse 23, 6003 Luzern](https://goldschmied-limacher.ch/kontakt/)

### Key Features

- **👀 Interactive Tracking**: The Dragon King puppet tracks visitors as they move in front of the window.
- **👋 Gesture Recognition**: Waves from visitors trigger pre-programmed carnival preparation sequences and custom dances.
- **⚡️ Modern Web Interface**: A greatly improved, responsive web-based maintenance interface for real-time adjustments, monitoring, and debugging.
- **🎨 Animation Studio**: Create and fine-tune movements using the integrated keyframe editor.

<!-- [![Watch the Demo](docs/images/video-thumbnail.png)](https://www.youtube.com/watch?v=YOUR_VIDEO_LINK) -->

### Privacy & Security

We respect visitor privacy:
- **🔒 Local Processing**: All AI processing happens on-device; the system is air-gapped (not connected to the internet).
- **🗂️ No Recording**: Images from the camera are processed for pose data in RAM and never saved to disk.
- **🛡️ Secure Access**: The maintenance interface is only accessible via the local physical network.

---

## 📊 Technical Details

### Hardware

The diorama is powered by a **Raspberry Pi 4 Model B**, serving as the central brain.
- **Actuation**: Controls multiple servo motors for the Dragon King and the surrounding "carnival preparation" figures.
- **Vision**: A camera module captures video for real-time pose estimation.
- **Lighting**: Integrated LED control for atmospheric effects.

### Software

The software stack has been updated for 2025:
- **Core**: Python 3.11 with [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) for robust, offline pose detection.
- **Orchestration**: A custom state machine manages visitor interactions and transitions between "Idle", "Observer", and "Show" states.
- **Web UI**: A completely overhauled Flask/WebUI interface allows not just for control, but for complex animation scheduling and system diagnostics.

---

## 🔧 Installation

To set up the software environment:

```bash
# Clone the repository
git clone https://github.com/pascscha/drachenland.git

# Install dependencies
pip install -r requirements.txt

# Configure GPIO pins
cp config/default.json.example config/default.json
# Edit config/default.json to match your specific servo/pin setup
```

---

## 🚀 Operation

### Starting the System

Run the main program with your configuration:

```bash
python main.py --config config/default.json
```

### Web Interface

Access the new maintenance dashboard on your local network at:

```
http://[raspberry-pi-ip]:5000
```
*(Note: Port defaults to 5000, configurable via arguments)*

### Physical Controls

The diorama includes manual override switches for on-site control:
- **Start switch**: Manually triggers the main show/animation sequence.
- **Test switch**: Runs a hardware diagnostic sequence.
- **Freigabe (Release) switch**: Master enable/disable for the entire system (stops all movement).

### Creating Animations

1. Open the **Animation Editor** in the web interface.
2. Design movements using the timeline and keyframe tools.
3. Save and export as `.json`.
4. Place the file in the `animations/` directory (or upload via UI).
5. The system will index the new animation automatically on restart.
