from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():

    result = ""
    waiting_time = ""
    alert = ""
    result_class = ""

    if request.method == "POST":

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