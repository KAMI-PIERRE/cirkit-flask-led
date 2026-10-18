from flask import Flask, render_template, jsonify

app = Flask(__name__)

# LED state
led_state = {
    "status": "OFF"
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/led/on", methods=["POST"])
def led_on():

    led_state["status"] = "ON"

    return jsonify(led_state)


@app.route("/led/off", methods=["POST"])
def led_off():

    led_state["status"] = "OFF"

    return jsonify(led_state)


@app.route("/api/led", methods=["GET"])
def get_led_status():

    return jsonify(led_state)


if __name__ == "__main__":
    app.run(debug=True)