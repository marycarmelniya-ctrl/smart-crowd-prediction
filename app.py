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

    if request.method == "POST":
        try:
            entries = int(request.form["entries"])
            exits = int(request.form["exits"])
            capacity = int(request.form["capacity"])
            exit_doors = int(request.form["exit_doors"])

            # -------- STRICT VALIDATION --------
            if entries <= 0:
                alert = "Invalid input: Entries must be greater than 0"

            elif exits < 0:
                alert = "Invalid input: Exits cannot be negative"

            elif exits > entries:
                alert = "Invalid input: Exits cannot exceed entries"

            elif capacity <= 0:
                alert = "Invalid input: Capacity must be greater than 0"

            elif exit_doors <= 0:
                alert = "Invalid input: Exit doors must be greater than 0"

            else:
                current_people = entries - exits
                current_people = min(current_people, capacity)

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

                # Risk Score
                exit_factor = 1 / exit_doors
                risk_score = round((density * 70) + (exit_factor * 30), 2)

                # Evacuation
                flow_rate = 50
                evac_time = round(current_people / (exit_doors * flow_rate), 2)

                # Alert logic
                if density > 0.75 and exit_doors < 2:
                    alert = "🚨 High Crowd + Low Exit Doors = Emergency Risk!"
                elif density > 0.75:
                    alert = "⚠ High Crowd – Monitor Situation"
                else:
                    alert = "Safe Environment"

        except ValueError:
            alert = "Invalid input detected. Please enter valid numbers."

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


if __name__ == "__main__":
    app.run(debug=True)