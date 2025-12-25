[**🇬🇧 English**](README.md) | [🇨🇭 Deutsch](README-DE.md)

# Drachenland Diorama  
![Python](https://img.shields.io/badge/python-3.11-blue.svg) ![License](https://img.shields.io/github/license/pascscha/drachenland)  

![Diorama in Action](docs/images/wave.gif)

## 🐲 About the Project
This project controls an interactive diorama featuring a central Dragon King puppet and surrounding dragon and serpent figures.

The exhibit will be displayed from **January to beginning of March 2025** at:

> [**Goldschmied Armin Limacher**](https://goldschmied-limacher.ch/kontakt/)
>
> [Pilatusstrasse 23, 6003 Luzern](https://goldschmied-limacher.ch/kontakt/)

### Key Features

- 👀 The Dragon King puppet tracks visitors as they move
- 👋 Waves from visitors trigger Pre-programmed dance sequences and custom animations
- 🔧 A web-based maintenance interface for adjustments and monitoring
- ✍️ Animation creation through an easy-to-use keyframe editor

<!-- [![Watch the Demo](docs/images/video-thumbnail.png)](https://www.youtube.com/watch?v=YOUR_VIDEO_LINK) -->

### Privacy

We respect your privacy:
- 🔒 All processing happens on the device, the system is not connected to the internet
- 🗂️ Images from the camera are never saved
- 🖥️ The maintenance interface is not accessible remotely

---

## 📊 Technical Details

### Hardware

The diorama is powered by a Raspberry Pi 4 Model B, which serves as the central control unit for the system. It controls servo motors that actuate the movement of the puppet, with precise control of the puppet's pose. A camera is used for pose detection, enabling the diorama to percieve and interact with visitors based on their movements.

### Software

The software driving the diorama is written in Python, using [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) for offline on-device pose detection. A Flask-based web interface allows for easy configuration and maintenance. The system includes custom-built animation and behavior control mechanisms, alongside a state machine that manages the interaction with the visitor and transitions between animations.

---

## 🔧 Installation

While replicating the exact hardware setup is unlikely, you can follow these steps to install the software:

```bash
# Clone the repository
git clone https://github.com/pascscha/drachenland.git

# Install dependencies
pip install -r requirements.txt

# Configure GPIO pins
cp config/default.json.example config/default.json
# Edit config/default.json to match your GPIO setup
```

---

### Starting the System

Run the main program with your configuration:

```bash
python main.py --config config/default.json
```

### Web Interface

Access the maintenance dashboard on your local network at:

```
http://[raspberry-pi-ip]:5001
```

### Physical Controls

The diorama includes manual override switches:
- **Start switch**: Trigger animations as if a visitor waved
- **Test switch**: Start a test sequence
- **Freigabe switch**: Disable all animations

### Creating Animations

1. Open the animation editor through the web interface.
2. Design movements using keyframes and export as `.json`.
3. Place the exported file into the `animations/` directory.
4. Restart the system to load your custom animations.
