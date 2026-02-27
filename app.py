from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():

    result = ""
    waiting_time = ""
    alert = ""
    result_class = ""

    if request.method == "POST":
        exit_doors = int(request.form["exit_doors"])

current_people = entries - exits
if current_people < 0:
    current_people = 0

density = current_people / capacity
density_percent = round(density * 100, 2)

        entries = int(request.form["entries"])
        exits = int(request.form["exits"])
        capacity = int(request.form["capacity"])

        if capacity <= 0:
            result = "Invalid Capacity"
            waiting_time = "-"
            alert = "Capacity must be greater than 0"
            result_class = "medium"
        else:
            current_people = entries - exits
            density = current_people / capacity

            if density < 0.4:
                result = "Low Crowd"
                waiting_time = "2 minutes"
                alert = "Safe environment"
                result_class = "low"

            elif density < 0.75:
                result = "Medium Crowd"
                waiting_time = "5 minutes"
                alert = "Monitor crowd movement"
                result_class = "medium"

            else:
                result = "High Crowd"
                waiting_time = "10 minutes"
                alert = "⚠ Overcrowding warning!"
                result_class = "high"

    return render_template(
        "index.html",
        result=result,
        waiting_time=waiting_time,
        alert=alert,
        result_class=result_class
    )

if __name__ == "__main__":
    app.run(debug=True)
exit_factor = 1 / exit_doors if exit_doors > 0 else 1
risk_score = round((density * 70) + (exit_factor * 30), 2)
flow_rate = 50  # people per minute per door
evac_time = round(current_people / (exit_doors * flow_rate), 2)
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
    evac_time=evac_time
)
