from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import threading
import json
import time
import os

app = Flask(__name__)

# ==========================================
# MQTT CONFIGURATION
# ==========================================

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

MQTT_TOPIC = "kami/cirkit/weight/data"

# ==========================================
# SHARED SENSOR DATA
# ==========================================

sensor_data = {
    "weight_kg": 0,
    "threshold_kg": 3.0,
    "led": "OFF",
    "buzzer": "OFF",
    "alert": "NORMAL",
    "last_update": None,
    "connected": False
}

data_lock = threading.Lock()

# ==========================================
# MQTT CALLBACKS
# ==========================================

def on_connect(client, userdata, flags, reason_code, properties):

    print("MQTT connection result:", reason_code)

    if reason_code == 0:

        client.subscribe(MQTT_TOPIC)

        print("Subscribed to:", MQTT_TOPIC)


def on_message(client, userdata, msg):

    try:

        payload = msg.payload.decode("utf-8")

        data = json.loads(payload)

        weight = float(data["weight_kg"])

        if not (0 <= weight <= 100000):
            raise ValueError("Invalid weight")

        threshold = 3.0

        alert_active = weight >= threshold

        with data_lock:

            sensor_data["weight_kg"] = weight

            sensor_data["threshold_kg"] = threshold

            sensor_data["led"] = (
                "ON" if alert_active else "OFF"
            )

            sensor_data["buzzer"] = (
                "ON" if alert_active else "OFF"
            )

            sensor_data["alert"] = (
                "THRESHOLD_REACHED"
                if alert_active
                else "NORMAL"
            )

            sensor_data["last_update"] = time.time()

            sensor_data["connected"] = True

        print("Received MQTT:", data)

    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:

        print("Invalid MQTT message:", e)


def on_disconnect(client, userdata, disconnect_flags,
                  reason_code, properties):

    print("MQTT disconnected:", reason_code)


# ==========================================
# MQTT CLIENT
# ==========================================

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect


def start_mqtt():

    try:

        mqtt_client.connect(
            MQTT_BROKER,
            MQTT_PORT,
            keepalive=60
        )

        mqtt_client.loop_forever()

    except Exception as e:

        print("MQTT error:", e)


# ==========================================
# FLASK ROUTES
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


@app.route("/api/weight")
def get_weight():

    with data_lock:

        data = sensor_data.copy()

    last_update = data["last_update"]

    data["connected"] = (
        last_update is not None
        and time.time() - last_update < 10
    )

    return jsonify(data)


@app.route("/health")
def health():

    return jsonify({
        "server": "online",
        "service": "IoT Weight Monitoring System"
    })


# ==========================================
# START MQTT THREAD
# ==========================================

mqtt_thread = threading.Thread(
    target=start_mqtt,
    daemon=True
)

mqtt_thread.start()


# ==========================================
# START FLASK
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )