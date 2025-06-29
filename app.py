from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "xja02PHdAG7bj9oVXfUchUFSF1UkDPz3wqrK3mwteHbq"
PROJECT_ID = "fd702cf2-878c-42d0-9b83-fba740170c5b"

def get_iam_token():
    res = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={API_KEY}"
    )
    return res.json().get("access_token")

def extract_json(text):
    match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return re.sub(r"```(json)?", "", text).strip()

@app.route("/generate", methods=["POST"])
def generate_erd():
    data = request.get_json()
    input_text = data.get("prompt", "")
    token = get_iam_token()

    model_payload = {
        "model_id": "ibm/granite-3-8b-instruct",
        "input": f"Convert this into an ERD JSON: '{input_text}'",
        "parameters": {
            "max_new_tokens": 1000,
            "temperature": 0.7
        },
        "project_id": PROJECT_ID
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2024-05-30",
        headers=headers,
        json=model_payload
    )

    print("Status code:", response.status_code)
    print("Raw text response:", response.text)

    try:
        result = response.json()
        raw = result["results"][0]["generated_text"]
        clean = extract_json(raw)
        return jsonify({ "output": clean })
    except Exception:
        return jsonify({
            "error": "Failed to parse model response.",
            "status_code": response.status_code,
            "details": response.text
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
