from flask import Flask, render_template, request, jsonify, session, send_file
import random, time, json, io, csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "aeroguard-local-demo-change-me"
SCENARIOS = {}  # Local in-memory store avoids oversized browser session cookies.

ENVIRONMENTS = ["Urban", "Rural", "Critical Infrastructure"]
WEATHER = ["Clear", "Fog", "Rain", "Crosswind"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]

def build_scenario(environment="Urban", weather="Clear", difficulty="Beginner", threat_mode="Mixed"):
    difficulty_level = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}.get(difficulty, 1)
    count = random.randint(3, 5) + (difficulty_level - 1) * 2
    count = min(count, 10)
    objects = []
    for i in range(count):
        # Synthetic training labels only; no live sensors, tracking, or control.
        is_threat = random.random() < (0.28 + 0.10 * (difficulty_level - 1))
        if threat_mode == "Single threat":
            is_threat = (i == random.randrange(count))
        elif threat_mode == "Swarm pattern":
            is_threat = i < min(3 + difficulty_level, count)
        kind = random.choice(["Multirotor", "Fixed-wing", "Unknown aerial object"])
        objects.append({
            "id": f"TRK-{random.randint(100,999)}",
            "kind": kind,
            "x": random.randint(8, 92),
            "y": random.randint(10, 88),
            "confidence": random.randint(58, 99),
            "signal": random.choice(["Low", "Medium", "High"]),
            "truth": "Threat" if is_threat else "Benign",
            "behavior": random.choice(["Steady transit", "Loitering", "Erratic path", "Leaving area", "Approaching zone"])
        })
    # Ensure a training event exists.
    if not any(o["truth"] == "Threat" for o in objects):
        objects[0]["truth"] = "Threat"
    return {
        "id": f"AG-{datetime.now().strftime('%H%M%S')}-{random.randint(10,99)}",
        "environment": environment, "weather": weather, "difficulty": difficulty,
        "threat_mode": threat_mode, "objects": objects,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "events": [], "actions": {}, "status": "active"
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/scenario")
def new_scenario():
    data = request.get_json(force=True)
    scenario = build_scenario(
        data.get("environment", "Urban"),
        data.get("weather", "Clear"),
        data.get("difficulty", "Beginner"),
        data.get("threat_mode", "Mixed")
    )
    SCENARIOS[scenario["id"]] = scenario
    session["scenario_id"] = scenario["id"]
    return jsonify(scenario)

@app.get("/api/scenario")
def current_scenario():
    scenario = SCENARIOS.get(session.get("scenario_id"))
    return jsonify(scenario or {})

@app.post("/api/action")
def action():
    data = request.get_json(force=True)
    scenario = SCENARIOS.get(session.get("scenario_id"))
    if not scenario or scenario.get("status") != "active":
        return jsonify({"error": "Start a new scenario first."}), 400
    track_id = data.get("track_id")
    classification = data.get("classification")
    response = data.get("response")
    valid_classes = ["Threat", "Benign", "Uncertain"]
    valid_responses = ["Continue monitoring", "Notify supervisor", "Simulated protective protocol"]
    if classification not in valid_classes or response not in valid_responses:
        return jsonify({"error": "Choose a valid training action."}), 400
    obj = next((o for o in scenario["objects"] if o["id"] == track_id), None)
    if not obj:
        return jsonify({"error": "Track not found."}), 404
    scenario["actions"][track_id] = {
        "classification": classification, "response": response,
        "truth": obj["truth"], "behavior": obj["behavior"],
        "confidence": obj["confidence"], "time": datetime.now().isoformat(timespec="seconds")
    }
    scenario["events"].append(f"{track_id}: classified as {classification}; response: {response}.")
    SCENARIOS[scenario["id"]] = scenario
    return jsonify({"ok": True, "scenario": scenario})

@app.post("/api/finish")
def finish():
    scenario = SCENARIOS.get(session.get("scenario_id"))
    if not scenario:
        return jsonify({"error": "No scenario available."}), 400
    actions = scenario.get("actions", {})
    objects = scenario["objects"]
    correct = 0
    points = 0
    details = []
    for obj in objects:
        action = actions.get(obj["id"])
        if not action:
            details.append({"track_id": obj["id"], "truth": obj["truth"], "classification": "Not reviewed", "result": "Missed"})
            continue
        correct_class = action["classification"] == obj["truth"]
        if correct_class:
            correct += 1
            points += 10
        elif action["classification"] == "Uncertain":
            points += 3
        # Reward proportionate, safety-oriented escalation for likely threats.
        if obj["truth"] == "Threat" and action["response"] in ["Notify supervisor", "Simulated protective protocol"]:
            points += 5
        elif obj["truth"] == "Benign" and action["response"] == "Continue monitoring":
            points += 5
        elif obj["truth"] == "Benign" and action["response"] == "Simulated protective protocol":
            points -= 3
        details.append({
            "track_id": obj["id"], "truth": obj["truth"],
            "classification": action["classification"],
            "response": action["response"],
            "result": "Correct" if correct_class else ("Cautious / review" if action["classification"] == "Uncertain" else "Incorrect")
        })
    max_points = len(objects) * 15
    score = max(0, round(points / max_points * 100)) if max_points else 0
    reviewed = len(actions)
    scenario["status"] = "completed"
    scenario["report"] = {
        "score": score, "correct": correct, "reviewed": reviewed, "total": len(objects),
        "details": details, "completed_at": datetime.now().isoformat(timespec="seconds"),
        "recommendation": "Repeat with a higher difficulty." if score >= 80 else "Review missed tracks and repeat the scenario."
    }
    SCENARIOS[scenario["id"]] = scenario
    return jsonify(scenario["report"])

@app.get("/api/report.json")
def report_json():
    scenario = SCENARIOS.get(session.get("scenario_id"))
    if not scenario or "report" not in scenario:
        return jsonify({"error": "Finish a scenario before exporting a report."}), 400
    return send_file(io.BytesIO(json.dumps(scenario, indent=2).encode()), mimetype="application/json",
                     as_attachment=True, download_name=f"{scenario['id']}_after_action_report.json")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
