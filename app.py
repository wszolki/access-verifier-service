from flask import Flask, request, jsonify
import requests
import json
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Lista adresów IP dozwolonych z AWS (inicjalizacja)
allowed_ips = set()
AWS_IP_RANGES_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
AWS_REGION = "eu-west-1"

# Funkcja do pobierania i filtrowania adresów IP z AWS
def update_allowed_ips():
    global allowed_ips
    try:
        response = requests.get(AWS_IP_RANGES_URL)
        response.raise_for_status()
        data = response.json()

        # Filtrowanie adresów z odpowiedniego regionu
        new_allowed_ips = set(
            prefix["ip_prefix"]
            for prefix in data["prefixes"]
            if prefix["region"] == AWS_REGION
        )
        allowed_ips = new_allowed_ips
        app.logger.info(f"Allowed IPs updated: {allowed_ips}")
    except Exception as e:
        app.logger.error(f"Failed to update allowed IPs: {e}")

# Endpoint do weryfikacji adresu IP
@app.route("/verify", methods=["POST"])
def verify_access():
    client_ip = request.remote_addr
    app.logger.info(f"Request received from IP: {client_ip}")

    if client_ip in allowed_ips:
        return "", 200
    else:
        return "", 401

# Inicjalizacja harmonogramu
scheduler = BackgroundScheduler()
scheduler.add_job(update_allowed_ips, "interval", hours=24)
scheduler.start()

# Aktualizacja listy adresów IP przy starcie aplikacji
update_allowed_ips()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
