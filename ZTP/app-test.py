from flask import Flask, request, Response, send_from_directory, abort, jsonify
import json
import os

app = Flask(__name__)
# 打开Debug
app.debug = True

# 配置基础文件存储路径
BASE_UPLOAD_FOLDER = '/app/image'
app.config['UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER

# 定义子文件夹路径
DEVICE_FOLDERS = {
    'Routers': os.path.join(BASE_UPLOAD_FOLDER, 'Routers'),
    'Switchs': os.path.join(BASE_UPLOAD_FOLDER, 'Switchs'),
    'Wireless': os.path.join(BASE_UPLOAD_FOLDER, 'Wireless')
}

# 确保所有子文件夹存在
for folder in DEVICE_FOLDERS.values():
    if not os.path.exists(folder):
        os.makedirs(folder)

# 从文件读取设备初始化配置
config_file_path = '/app/flask_app/device_init_config.cfg'
with open(config_file_path, 'r') as file:
    device_init_config = file.read()

config_list = [c for c in device_init_config.split('\n') if c]

######## 测试代码
@app.route('/device_config/<device_sn>', methods=['GET'])
def device_config(device_sn):
    if device_sn == 'FOC2327X0K8':
        return Response(response=json.dumps({'config': config_list}),
                        status=200,
                        mimetype='application/json')
    else:
        return jsonify({'config': []})

@app.route('/device_config_json', methods=['POST'])
def device_config_json():
    client_post_data = request.json
    if client_post_data:
        device_sn = client_post_data.get('device_sn')
        device_ip = client_post_data.get('device_ip')
        if device_sn == 'FOC2327X0K8':
            return Response(response=json.dumps({'config': config_list}),
                            status=200,
                            mimetype='application/json')
        else:
            return jsonify({'config': []})
    else:
        return jsonify({'config': []})

@app.route('/download/<device_type>/<filename>', methods=['GET'])
def download_file(device_type, filename):
    if device_type in DEVICE_FOLDERS:
        return send_from_directory(DEVICE_FOLDERS[device_type], filename, as_attachment=True)
    else:
        return 'Invalid device type', 400

@app.route('/day0-ztp.py', methods=['GET'])
def serve_ztp_sample():
    file_path = '/app/flask_app/day0-ztp.py'
    if os.path.exists(file_path):
        return send_from_directory('/app/flask_app', 'day0-ztp.py')
    else:
        return abort(404, description="File not found")

@app.route('/download', methods=['GET'])
def list_files():
    files = {}
    for root, dirs, filenames in os.walk(BASE_UPLOAD_FOLDER):
        # 获取相对路径
        relative_root = os.path.relpath(root, BASE_UPLOAD_FOLDER)
        if relative_root == '.':
            relative_root = ''
        files[relative_root] = filenames

    # 创建HTML内容
    html_content = "<h1>Files and Directories in /app/image</h1><ul>"
    for folder, filenames in files.items():
        if folder:
            html_content += f"<h2>{folder}</h2><ul>"
        for filename in filenames:
            file_url = f"/download/{folder}/{filename}" if folder else f"/download/{filename}"
            html_content += f'<li><a href="{file_url}">{filename}</a></li>'
        if folder:
            html_content += "</ul>"
    html_content += "</ul>"

    return html_content

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)