from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    waiting_time = None
    alert = None
    result_class = ""
    density_percent = None
    risk_score = None
    evac_time = None
    location = None

    if request.method == "POST":
        location = request.form["location"]
        entries = int(request.form["entries"])
        exits = int(request.form["exits"])
        capacity = int(request.form["capacity"])
        exit_doors = int(request.form["exit_doors"])

        # Safety checks
        if capacity <= 0:
            alert = "Capacity must be greater than 0"
            return render_template("index.html", alert=alert)

        if exits > entries:
            exits = entries

        current_people = entries - exits

        # Density
        density = current_people / capacity
        density_percent = round(density * 100, 2)

        # Crowd classification
        if density < 0.4:
            result = "Low Crowd"
            waiting_time = "2 minutes"
            result_class = "low"
        elif density < 0.75:
            result = "Medium Crowd"
            waiting_time = "5 minutes"
            result_class = "medium"
        else:
            result = "High Crowd"
            waiting_time = "10 minutes"
            result_class = "high"

        # Risk score
        exit_factor = 1 / exit_doors if exit_doors > 0 else 1
        risk_score = round((density * 70) + (exit_factor * 30), 2)

        # Evacuation time
        flow_rate = 50
        if exit_doors > 0:
            evac_time = round(current_people / (exit_doors * flow_rate), 2)
        else:
            evac_time = "Not possible (No exit doors)"

        # Alert logic
        if density > 0.75 and exit_doors < 2:
            alert = "🚨 High Crowd + Low Exit Doors = Emergency Risk!"
        elif density > 0.75:
            alert = "⚠ High Crowd – Monitor Situation"
        else:
            alert = "Safe Environment"

    return render_template(
        "index.html",
        result=result,
        waiting_time=waiting_time,
        alert=alert,
        result_class=result_class,
        density_percent=density_percent,
        risk_score=risk_score,
        evac_time=evac_time,
        location=location
    )

if __name__ == "__main__":
    app.run(debug=True)