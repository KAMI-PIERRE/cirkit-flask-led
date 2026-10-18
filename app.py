import os
import time
import uuid

from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt

app = Flask(__name__)

# ==========================================
# MQTT CONFIGURATION
# ==========================================

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

MQTT_TOPIC = "kami/cirkit/led/control"

# Track the most recently requested state.
# This is not confirmation of the physical/simulated LED state.
led_state = {
    "status": "OFF"
}


# ==========================================
# PUBLISH MQTT COMMAND
# ==========================================

def publish_mqtt_command(command):
    client_id = f"flask-led-{uuid.uuid4().hex[:12]}"

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id
    )

    try:
        print(f"Connecting to MQTT broker: {MQTT_BROKER}")

        client.connect(
            MQTT_BROKER,
            MQTT_PORT,
            keepalive=30
        )

        client.loop_start()

        # Give the client time to establish its connection.
        deadline = time.time() + 5

        while not client.is_connected() and time.time() < deadline:
            time.sleep(0.1)

        if not client.is_connected():
            raise TimeoutError("MQTT connection timed out")

        info = client.publish(
            MQTT_TOPIC,
            payload=command,
            qos=0,
            retain=False
        )

        info.wait_for_publish(timeout=5)

        if not info.is_published():
            raise TimeoutError("MQTT message was not confirmed as sent")

        print(f"Published {command} to {MQTT_TOPIC}")

        return True, None

    except Exception as error:
        print(f"MQTT error: {error}")
        return False, str(error)

    finally:
        try:
            if client.is_connected():
                client.disconnect()

            client.loop_stop()

        except Exception:
            pass


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# LED ON
# ==========================================

@app.route("/led/on", methods=["POST"])
def led_on():

    success, error = publish_mqtt_command("ON")

    if not success:
        return jsonify({
            "status": led_state["status"],
            "success": False,
            "message": "Could not send the ON command.",
            "error": error
        }), 502

    led_state["status"] = "ON"

    return jsonify({
        "status": "ON",
        "success": True,
        "message": "ON command published successfully."
    })


# ==========================================
# LED OFF
# ==========================================

@app.route("/led/off", methods=["POST"])
def led_off():

    success, error = publish_mqtt_command("OFF")

    if not success:
        return jsonify({
            "status": led_state["status"],
            "success": False,
            "message": "Could not send the OFF command.",
            "error": error
        }), 502

    led_state["status"] = "OFF"

    return jsonify({
        "status": "OFF",
        "success": True,
        "message": "OFF command published successfully."
    })


# ==========================================
# LED STATUS API
# ==========================================

@app.route("/api/led", methods=["GET"])
def get_led_status():

    return jsonify({
        "status": led_state["status"]
    })


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "server": "online",
        "message": "Flask LED Control API is running"
    })


# ==========================================
# RUN LOCALLY
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)