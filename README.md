# Rapid Serial Visual Presentation (RSVP) Reader

Interactive speed-reading application built with Python and Kivy featuring gesture controls, dynamic playback customization, and custom text rendering systems inspired by RSVP platforms such as Spritz.

This project focuses on event-driven UI architecture, rendering systems, accessibility-oriented interface design, and real-time playback interaction.

---

## Features

- Dynamic RSVP playback with adjustable words-per-minute (WPM)
- Gesture-based and keyboard-driven playback controls
- Real-time pause, rewind, and playback speed adjustment
- Configurable fonts, font sizes, and display preferences
- Interactive file loading for custom text playback
- Custom focus-character alignment and visual text guidance system
- Responsive cross-platform UI scaling using device-independent rendering
- Accessibility-focused reading experience with dyslexia-friendly font support

---

## Playback Controls

### Keyboard Controls
- Left Arrow → Jump backward in playback timeline
- Right Arrow → Jump forward in playback timeline
- Up Arrow → Increase playback speed
- Down Arrow → Decrease playback speed
- `+` / `=` → Increase font size
- `-` → Decrease font size
- Spacebar → Pause / Resume playback

### Gesture Controls
- Swipe Left → Jump backward
- Swipe Right → Jump forward
- Swipe Up → Increase playback speed
- Swipe Down → Decrease playback speed
- Tap → Pause / Resume playback

---

## Technical Highlights

### Custom Text Rendering
Implemented glyph-aware rendering logic using:
- `freetype-py`
- `uharfbuzz`
- custom font metric calculations

to dynamically align each word’s focus character to a fixed visual center point during playback.

### Event-Driven Playback System
Built a real-time scheduling system using the Kivy Clock API to:
- dynamically control word timing
- support playback interruption and resumption
- scale display duration based on word complexity and reading speed

### Responsive UI Architecture
Designed scalable UI systems using:
- Kivy ScreenManager
- reusable interface components
- device-independent rendering (`dp`)
- event-driven interaction handling

---

## Technologies

- Python
- Kivy
- freetype-py
- uharfbuzz
- Object-Oriented Programming
- Event-Driven UI Systems
- Gesture Recognition
- Responsive UI Design

---

## Running the Application

### Requirements
- Python 3.11+
- Kivy
- freetype-py
- uharfbuzz

### Run
```bash
python main.py
