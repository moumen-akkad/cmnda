from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/op", methods=["POST"])
def delegated_operation():
    # BaSyx sends the operation parameters as JSON array
    data = request.get_json(force=True, silent=True) or []
    print("Delegated operation called with args:", data)

    # Here you can do anything; just printing to stdout
    print("Hello from delegated op!")

    # Return result in JSON array (BaSyx expects this format)
    return jsonify(["Operation executed OK"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
