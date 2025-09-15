# delegate_service.py
import os
import json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Default BaSyx property value endpoint for pumpValue (/value is important)
BASYX_PUMP_VALUE_URL = os.getenv(
    "BASYX_PUMP_VALUE_URL",
    "http://localhost:8081/submodels/dXJuOmV4YW1wbGU6c206b3BzOjE/submodel-elements/pumpValue/$value",
)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/op", methods=["POST"])
@app.route("/op", methods=["POST"])
def delegated_operation():
    data = request.get_json(force=True, silent=True) or {}
    print(f"Received delegated operation call with data: {data}")

    pump_value = None

    # Case 1: AAS-style input arguments (list of dicts)
    if isinstance(data, list):
        try:
            # Find the property argument with idShort = pumpValue (or ExamplePropertyInput)
            for arg in data:
                val = arg.get("value", {})
                if val.get("idShort") in ("pumpValue", "ExamplePropertyInput"):
                    pump_value = val.get("value")
                    break
        except Exception as e:
            return jsonify({"error": f"Invalid input argument structure: {e}"}), 400

    # Case 2: Simple JSON body {"pumpValue": "123"}
    elif isinstance(data, dict) and "pumpValue" in data:
        pump_value = data["pumpValue"]

    if pump_value is None:
        return jsonify({"error": "pumpValue (or ExamplePropertyInput) not found in request"}), 400

    # Prepare JSON body for BaSyx: /value expects the raw JSON value
    try:
        body = json.dumps(pump_value)
        headers = {"Content-Type": "application/json"}
        basyx_resp = requests.patch(
            BASYX_PUMP_VALUE_URL, data=body, headers=headers, timeout=5
        )

        if not basyx_resp.ok:
            return jsonify({
                "message": "BaSyx update failed",
                "status_code": basyx_resp.status_code,
                "text": basyx_resp.text,
            }), 502

        return jsonify({
            "message": "Operation executed",
            "wrote": pump_value,
            "basyx_url": BASYX_PUMP_VALUE_URL,
        }), 200

    except requests.RequestException as e:
        return jsonify({"message": "Network error contacting BaSyx", "error": str(e)}), 502
    except Exception as e:
        return jsonify({"message": "Unexpected error", "error": str(e)}), 500

if __name__ == "__main__":
    # Bind to all interfaces for docker-compose friendliness
    app.run(host="0.0.0.0", port=5001)
