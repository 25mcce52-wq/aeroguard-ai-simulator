# AeroGuard AI Simulator — SIH 2026 Working Prototype

A local, browser-based **defensive counter-UAS training simulator** aligned with the AeroGuard pitch:
- Procedural training scenario generation (urban, rural, critical infrastructure)
- Synthetic tracks with behavior, confidence and signal indicators
- Single-threat, mixed and swarm-pattern scenario modes
- Trainee classification and proportionate response decisions
- After-Action Review (AAR), scoring and JSON report export
- Adaptive difficulty options and weather settings

## Run on Windows
1. Install Python 3.10 or newer from https://www.python.org/downloads/ (tick **Add Python to PATH**).
2. Extract this ZIP to a folder.
3. Double-click `run_windows.bat`.
4. Wait for dependencies to install, then open **http://127.0.0.1:5000** in Chrome or Edge.
5. Keep the terminal window open while using the prototype. Press `Ctrl+C` in that window to stop it.

If Windows blocks the batch file, open Command Prompt in this folder and run:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Demo flow (recommended for SIH jury)
1. Select **Critical Infrastructure**, **Fog**, **Advanced**, and **Swarm pattern**.
2. Click **Generate scenario**.
3. Select each synthetic track, choose a classification and a response, and submit the decision.
4. Click **Finish & review** to show the score, missed detections and AAR.
5. Click **Export AAR JSON** to download a report.

## Honest prototype scope
This is a runnable software prototype using generated/synthetic tracks. It does not connect to real radar, cameras, drones, radio systems or counter-drone hardware, and does not issue real-world commands. The AI/behavior logic is currently a transparent simulation baseline rather than a trained PyTorch model. Unreal Engine/VR and WebRTC are future integration stages from the proposal, not implemented in this prototype.

## Project structure
- `app.py` — Flask backend, scenario generator, scoring and report API
- `templates/index.html` — simulator UI
- `static/style.css` — interface styling
- `static/app.js` — dashboard interactions
- `requirements.txt` — Python dependency
- `run_windows.bat` — one-click Windows launcher
