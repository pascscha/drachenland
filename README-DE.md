[🇬🇧 English](README.md) | [**🇨🇭 Deutsch**](README-DE.md)

# D'Vorfröid

Dieses Projekt steuert ein interaktives Diorama, das Menschen zeigt, die für die kommende Fasnacht basteln und sich vorbereiten. Das Diorama zeigt die Vorfreude und kreative Energie der Fasnachtsvorbereitung.

![Diorama in Aktion](docs/images/vorfreud.gif)

Die Ausstellung ist von **Januar bis ende Fasnacht 2026** zu sehen bei:

> [**Goldschmied Armin Limacher**](https://goldschmied-limacher.ch/kontakt/)
> [Pilatusstrasse 23, 6003 Luzern](https://goldschmied-limacher.ch/kontakt/)

## Was macht das Diorama besonders?

- **Es sieht dich!** Die Figuren im Diorama starten sich zu bewegen, wenn du vor dem Schaufenster stehst.
- **Lebendige Szenen**: Beobachte, wie die Figuren Masken basteln, Kostüme nähen und sich auf die Fasnacht vorbereiten
- **Alles lokal**: Die Kamera verarbeitet Bilder nur im Arbeitsspeicher und die gesamte Verarbeitung findet auf dem Gerät statt.

## Wie funktioniert's?

Das Diorama wird von einem kleinen Computer (Raspberry Pi) gesteuert, der:
- Mit einer Kamera deine Bewegungen erkennt
- Künstliche Intelligenz nutzt, um deine Posen zu verstehen
- Die Servomotoren der Figuren entsprechend steuert
- Alles komplett offline und ohne Internetverbindung macht

- **Steuerung**: Raspberry Pi 4 Model B
- **Bewegung**: Mehrere Servomotoren für die Figuren
- **Vision**: Kameramodul mit [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) für Posenerkennung (offline)

## Betrieb

Falls ihr zufällig selber dieses Diorama bei euch zu Hause rumstehen habt, könnt ihr natürlich die Software darauf starten!

```bash
# Repository klonen
git clone https://github.com/pascscha/drachenland.git

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration anpassen
cp config/default.json.example config/default.json

# System starten
python main.py --config config/default.json

# Weboberfläche öffnen
# http://[raspberry-pi-ip]:5000
```
