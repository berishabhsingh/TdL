import os
from flask import Flask, request, jsonify
from flowapi import get_flowvideo_links

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    url = request.args.get('url') or request.form.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = get_flowvideo_links(url)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
