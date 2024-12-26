[🇬🇧 English](README.md) | [**🇨🇭 Deutsch**](README-DE.md)

# Drachenland Diorama  
![Python](https://img.shields.io/badge/python-3.11-blue.svg) ![Lizenz](https://img.shields.io/github/license/pascscha/drachenland)  

![Diorama in Aktion](docs/images/wave.gif)

## 🐲 Über das Projekt
Dieses Projekt steuert ein interaktives Diorama mit einer zentralen Drachenkönig-Marionette sowie umliegenden Drachen- und Schlangenfiguren.

Die Ausstellung wird von **Januar bis Februar 2025** zu sehen sein bei:

> [**Goldschmied Armin Limacher**](https://goldschmied-limacher.ch/kontakt/)
>
> [Pilatusstrasse 23, 6003 Luzern](https://goldschmied-limacher.ch/kontakt/)

### Hauptmerkmale

- 👀 Die Drachenkönig-Marionette verfolgt Besucherbewegungen
- 👋 Winken von Besuchern löst vorprogrammierte Tanzsequenzen und individuelle Animationen aus
- 🔧 Eine webbasierte Wartungsschnittstelle für Anpassungen und Überwachung
- ✍️ Erstellung von Animationen mit einem benutzerfreundlichen Keyframe-Editor

<!-- [![Demo ansehen](docs/images/video-thumbnail.png)](https://www.youtube.com/watch?v=YOUR_VIDEO_LINK) -->

### Datenschutz

Wir respektieren Ihre Privatsphäre:
- 🔒 Alle Verarbeitungsvorgänge finden auf dem Gerät statt; das System ist nicht mit dem Internet verbunden
- 🗂️ Bilder von der Kamera werden unmittelbar nach der Verarbeitung gelöscht
- 🖥️ Die Wartungsschnittstelle ist nicht aus der Ferne zugänglich

---

## 📊 Technische Details

### Hardware

Das Diorama wird von einem Raspberry Pi 4 Model B gesteuert, der als zentrale Steuereinheit des Systems dient. Er kontrolliert Servomotoren, die die Bewegungen der Marionette mit präziser Positionskontrolle steuern. Eine Kamera wird für Pose-Detektion verwendet, wodurch das Diorama Besucherbewegungen wahrnehmen und darauf reagieren kann.

### Software

Die Software, die das Diorama antreibt, ist in Python geschrieben und verwendet [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) für die Offline-Pose-Detektion auf dem Gerät. Eine Flask-basierte Weboberfläche ermöglicht eine einfache Konfiguration und Wartung. Das System enthält speziell entwickelte Mechanismen für Animationen und Verhaltenssteuerung sowie einen Zustandsautomaten, der die Interaktion mit Besuchern und Übergänge zwischen Animationen verwaltet.

---

## 🔧 Installation

Auch wenn es schwierig sein könnte, die Hardware exakt nachzubauen, können Sie die Software wie folgt installieren:

```bash
# Repository klonen
git clone https://github.com/pascscha/drachenland.git

# Abhängigkeiten installieren
pip install -r requirements.txt

# GPIO-Pins konfigurieren
cp config/default.json.example config/default.json
# Bearbeiten Sie config/default.json, um Ihre GPIO-Konfiguration anzupassen
```

---

### System starten

Starten Sie das Hauptprogramm mit Ihrer Konfiguration:

```bash
python main.py --config config/default.json
```

### Weboberfläche

Greifen Sie auf das Wartungs-Dashboard im lokalen Netzwerk zu unter:

```
http://[raspberry-pi-ip]:5001
```

### Physische Steuerung

Das Diorama verfügt über manuelle Übersteuerungsschalter:
- **Start-Schalter**: Löst Animationen aus, als ob ein Besucher winkt
- **Test-Schalter**: Startet eine Testsequenz
- **Freigabe-Schalter**: Deaktiviert alle Animationen

### Animationen erstellen

1. Öffnen Sie den Animations-Editor über die Weboberfläche.
2. Entwerfen Sie Bewegungen mit Keyframes und exportieren Sie diese als `.json`.
3. Platzieren Sie die exportierte Datei im Verzeichnis `animations/`.
4. Starten Sie das System neu, um Ihre benutzerdefinierten Animationen zu laden.
