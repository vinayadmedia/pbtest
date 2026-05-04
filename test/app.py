import os
import re
import requests
from flask import Flask, render_template, request, jsonify

# Force Flask to find the templates folder correctly on Windows
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fire-test', methods=['POST'])
def fire_test():
    test_link = request.form.get('test_link')
    postback_tpl = request.form.get('postback_template')

    if not test_link or not postback_tpl:
        return jsonify({"status": "error", "message": "Missing URL inputs"}), 400

    try:
        # 1. Simulate the click and follow redirects
        session = requests.Session()
        # Using a browser-like User-Agent to avoid being blocked during the click
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        response = session.get(test_link, headers=headers, allow_redirects=True, timeout=15)
        final_url = response.url

        # 2. Extract the clickid using Regular Expression
        match = re.search(r'clickid=([a-zA-Z0-9\-]+)', final_url)
        
        if not match:
            return jsonify({
                "status": "error", 
                "message": "Click ID not found in redirect chain.",
                "final_url_reached": final_url
            })

        captured_id = match.group(1)

        # 3. Replace placeholders in the Postback Template
        # Note: We leave other placeholders alone unless you want to hardcode them
        fired_url = postback_tpl.replace("{clickid}", captured_id)

        # 4. Fire the Postback to Marketcall
        pb_response = requests.get(fired_url, timeout=15)

        # Determine if the server response looks like a success or error
        # Marketcall usually returns JSON with request_id
        return jsonify({
            "status": "success" if pb_response.status_code == 200 else "warning",
            "captured_id": captured_id,
            "final_landing_page": final_url,
            "fired_postback_url": fired_url,
            "http_code": pb_response.status_code,
            "server_response": pb_response.text  # This will show the "Merchant own id" error if missing
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)