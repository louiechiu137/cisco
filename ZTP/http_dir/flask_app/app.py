from flask import Flask, request, Response, send_from_directory, abort, jsonify, send_file
import json
import os
import csv

app = Flask(__name__)
app.debug = True

# Configure image folder
IMAGE_FOLDER = '/app/image'
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

# Ensure the base folder exists
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)
    print(f"Created directory: {IMAGE_FOLDER}")

# Paths to configuration files
config_file_path = '/app/flask_app/device_init_config.cfg'
device_init_stack_file_path = '/app/flask_app/device_init_stack.json'
csv_template_path = '/app/flask_app/new_quality_productivity.csv'

def read_device_init_config():
    with open(config_file_path, 'r') as file:
        return file.read().split('\n')

def read_device_init_stack():
    if os.path.exists(device_init_stack_file_path):
        with open(device_init_stack_file_path, 'r') as file:
            return json.load(file)
    else:
        return {}

@app.route('/device_config/<device_sn>', methods=['GET'])
def device_config(device_sn):
    try:
        config_list = read_device_init_config()
        device_init_stack = read_device_init_stack()

        config = config_list.copy()  # Copy base configuration
        response = {'config': config}

        # Find the stack group containing the given serial number
        for hostname, group_data in device_init_stack.items():
            for switch in group_data['switches']:
                if switch['serial_number'] == device_sn:
                    response.update({
                        'stack_priority': switch['stack_priority'],
                        'stack_number': switch['stack_number'],
                        'version_upgrade': group_data['config']['version_upgrade'],
                        'hostname': group_data['config']['hostname'],
                        'interface_vlan': group_data['config']['interface_vlan'],
                        'ip_address': group_data['config']['ip_address'],
                        'subnet_mask': group_data['config']['subnet_mask'],
                        'default_gateway': group_data['config']['default_gateway']
                    })
                    break

        return Response(response=json.dumps(response),
                        status=200,
                        mimetype='application/json')
    except Exception as e:
        print(f"Error reading device config: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/device_config_json', methods=['POST'])
def device_config_json():
    try:
        client_post_data = request.json
        config_list = read_device_init_config()
        device_init_stack = read_device_init_stack()

        response = {'config': config_list.copy()}  # Copy base configuration

        if client_post_data:
            device_sn = client_post_data.get('device_sn')
            device_ip = client_post_data.get('device_ip')

            # Find the stack group containing the given serial number
            for hostname, group_data in device_init_stack.items():
                for switch in group_data['switches']:
                    if switch['serial_number'] == device_sn:
                        response.update({
                            'stack_priority': switch['stack_priority'],
                            'stack_number': switch['stack_number'],
                            'version_upgrade': group_data['config']['version_upgrade'],
                            'hostname': group_data['config'].get('hostname'),
                            'interface_vlan': group_data['config']['interface_vlan'],
                            'ip_address': group_data['config']['ip_address'],
                            'subnet_mask': group_data['config']['subnet_mask'],
                            'default_gateway': group_data['config']['default_gateway']
                        })
                        break

        return Response(response=json.dumps(response),
                        status=200,
                        mimetype='application/json')
    except Exception as e:
        print(f"Error reading device config JSON: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_json', methods=['POST'])
def update_json():
    try:
        new_data = request.json
        print(f"Received JSON data: {json.dumps(new_data, indent=4)}")  # Debugging output
        with open(device_init_stack_file_path, 'w') as file:
            json.dump(new_data, file, indent=4)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating JSON file: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_config', methods=['POST'])
def update_config():
    try:
        new_config = request.data.decode('utf-8')
        with open(config_file_path, 'w') as file:
            file.write(new_config)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating config file: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})

    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(app.config['IMAGE_FOLDER'], file.filename)
        print(f"Saving file to: {filepath}")
        file.save(filepath)

        try:
            with open(filepath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                device_init_stack = {}

                for row in reader:
                    print(f"Processing row: {row}")
                    if 'hostname' not in row or 'serial_number' not in row or 'stack_priority' not in row or 'stack_number' not in row:
                        raise ValueError("CSV file missing required columns")

                    hostname = row['hostname']
                    if hostname not in device_init_stack:
                        device_init_stack[hostname] = {
                            "config": {
                                "version_upgrade": row['version_upgrade'],
                                "hostname": row['hostname'],
                                "interface_vlan": row['interface_vlan'],
                                "ip_address": row['ip_address'],
                                "subnet_mask": row['subnet_mask'],
                                "default_gateway": row['default_gateway']
                            },
                            "switches": []
                        }

                    device_init_stack[hostname]["switches"].append({
                        "serial_number": row['serial_number'],
                        "stack_priority": int(row['stack_priority']),
                        "stack_number": int(row['stack_number'])
                    })

                with open(device_init_stack_file_path, 'w') as jsonfile:
                    json.dump(device_init_stack, jsonfile, indent=4)

            return jsonify({"success": True})

        except Exception as e:
            print(f"Error processing CSV file: {e}")
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "Invalid file format"})

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})

    if file:
        filepath = os.path.join(app.config['IMAGE_FOLDER'], file.filename)
        try:
            print(f"Saving image to: {filepath}")
            file.save(filepath)
            print(f"File saved to {filepath}")
            return jsonify({"success": True, "filepath": filepath})
        except Exception as e:
            print(f"Error saving file: {e}")
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "Invalid file format"})

@app.route('/download_template', methods=['GET'])
def download_template():
    if os.path.exists(csv_template_path):
        return send_file(csv_template_path, as_attachment=True)
    else:
        return abort(404, description="Template file not found")

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(IMAGE_FOLDER, filename, as_attachment=True)

@app.route('/day0-ztp.py', methods=['GET'])
def serve_ztp_sample():
    file_path = '/app/flask_app/day0-ztp.py'
    if os.path.exists(file_path):
        return send_from_directory('/app/flask_app', 'day0-ztp.py')
    else:
        return abort(404, description="File not found")

@app.route('/')
def serve_index():
    return send_from_directory('/app/flask_app', 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)