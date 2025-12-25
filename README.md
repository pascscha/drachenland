[**🇬🇧 English**](README.md) | [🇨🇭 Deutsch](README-DE.md)

# The Anticipation

This project controls an interactive diorama showing people crafting and preparing for the upcoming Fasnacht. The diorama depicts the anticipation and creative energy of Fasnacht preparation.

![Diorama in Action](docs/images/Vorfröid.gif)

The exhibition can be seen from **January until the end of Fasnacht 2026** at:

> [**Goldschmied Armin Limacher**](https://goldschmied-limacher.ch/kontakt/)
>
> [Pilatusstrasse 23, 6003 Luzern](https://goldschmied-limacher.ch/kontakt/)

## What makes the diorama special?

- **It sees you!** The figures in the diorama start moving when you stand in front of the shop window.
- **Living scenes**: Watch as the figures craft masks, sew costumes, and prepare for Fasnacht
- **All local**: The camera processes images only in memory and all processing happens on the device.

## How does it work?

The diorama is controlled by a small computer (Raspberry Pi) that:
- Detects your movements with a camera
- Uses artificial intelligence to understand your poses
- Controls the servo motors of the figures accordingly
- Does everything completely offline without an internet connection

- **Control**: Raspberry Pi 4 Model B
- **Movement**: Multiple servo motors for the figures
- **Vision**: Camera module with [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) for pose detection (offline)

## Operation

If you happen to have this diorama sitting around at your home, you can of course run the software on it!
```bash
# Clone repository
git clone https://github.com/pascscha/drachenland.git

# Install dependencies
pip install -r requirements.txt

# Adjust configuration
cp config/default.json.example config/default.json

# Start system
python main.py --config config/default.json

# Open web interface
# http://[raspberry-pi-ip]:5000
```