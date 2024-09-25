# File location: /usr/local/cisco/ZTP/http_dir/flask_app

from cli import configurep, cli, executep
import json
import os
import time
import subprocess
import re

def get_switch_id_serial_mapping():
    """Parse 'show version' output to get a mapping of switch IDs to serial numbers"""
    version_output = cli('show version')
    switch_id_to_serial = {}
    lines = version_output.split('\n')
    num_lines = len(lines)
    i = 0

    while i < num_lines:
        line = lines[i]
        # Check if it's a 'Switch xx' line
        match = re.match(r'^Switch\s+(\d+)', line)
        if match:
            switch_id = match.group(1)
            serial_number = None
            # Search for 'System Serial Number' below
            i += 1
            while i < num_lines:
                sub_line = lines[i]
                sn_match = re.search(r'System Serial Number\s+:\s+(\S+)', sub_line)
                if sn_match:
                    serial_number = sn_match.group(1)
                    break
                elif re.match(r'^Switch\s+\d+', sub_line):
                    # Encountered next 'Switch', break loop
                    i -= 1  # Step back to process in outer loop
                    break
                i += 1
            if serial_number:
                switch_id_to_serial[switch_id] = serial_number
            else:
                print(f"Warning: Unable to find serial number for switch {switch_id}")
        elif 'System Serial Number' in line:
            # Handle main switch information
            sn_match = re.search(r'System Serial Number\s+:\s+(\S+)', line)
            if sn_match:
                serial_number = sn_match.group(1)
                # Get active switch ID
                switch_output = cli('show switch')
                active_switch_id = None
                for switch_line in switch_output.split('\n'):
                    if switch_line.strip().startswith('*'):
                        fields = switch_line.strip().split()
                        if len(fields) >= 1:
                            switch_indicator = fields[0]
                            active_switch_id = switch_indicator.lstrip('*')
                            break
                if active_switch_id:
                    switch_id_to_serial[active_switch_id] = serial_number
                else:
                    print("Warning: Unable to determine the active switch ID")
        i += 1
    print("Switch ID to Serial Number mapping:")
    print(switch_id_to_serial)
    return switch_id_to_serial

def deploy_eem_script(name, event_pattern, actions):
    """Generic function to deploy EEM scripts"""
    eem_commands = [f'event manager applet {name}', f'event {event_pattern}']
    eem_commands.extend(actions)
    configurep(eem_commands)
    print(f"Successfully configured '{name}' EEM script on the device.")

def main():
    print("\n*** Starting ZTP Day0 Python Script ***\n")

    # Define ZTP server address
    ztp_server = '10.0.0.131'

    # Get device model and serial number
    version_output = cli('show version')
    model_match = re.search(r"Model Number\s+:\s+(\S+)", version_output)
    sn_match = re.search(r"System Serial Number\s+:\s+(\S+)", version_output)

    model_number = model_match.group(1) if model_match else ''
    device_sn = sn_match.group(1) if sn_match else ''

    if not (model_number and device_sn):
        print("Error: Missing essential device information.")
        return

    # Set initial hostname
    hostname_init = f"{model_number}-{device_sn}"
    configurep([f"hostname {hostname_init}"])
    print(f"Initial hostname set to: {hostname_init}")

    # Get device IP address
    ip_output = cli('show ip interface brief')
    device_ip_match = re.search(r"(\S+)\s+DHCP", ip_output)
    device_ip = device_ip_match.group(1) if device_ip_match else ''

    # Prepare POST request data
    data = json.dumps({
        "model_number": model_number,
        "device_sn": device_sn,
        "device_ip": device_ip
    })

    # Send POST request and get response
    response = os.popen(
        f'curl -s -X POST -H "Content-Type: application/json" -d \'{data}\' http://{ztp_server}/device_config_json'
    ).read()
    response_data = json.loads(response)
    print("Received response data from ZTP server:")
    print(response_data)

    # Apply config template
    config_list = response_data.get('config_template', [])
    if config_list:
        configurep(config_list)
        print("Applied configuration template.")

    # Get all device keys excluding 'config_template'
    hostname_keys = [key for key in response_data.keys() if key != 'config_template']
    if not hostname_keys:
        print("No device configuration found in the response.")
        return

    # Process configurations for each device
    for hostname_key in hostname_keys:
        device_data = response_data[hostname_key]
        config_data = device_data.get('config', {})
        switches_data = device_data.get('switches', [])

        # Apply device-specific configurations
        hostname = config_data.get('hostname')
        version_upgrade = config_data.get('version_upgrade')
        interface_vlan = config_data.get('interface_vlan')
        ip_address = config_data.get('ip_address')
        subnet_mask = config_data.get('subnet_mask')
        default_gateway = config_data.get('default_gateway')

        # Build and apply additional commands
        other_commands = []
        if hostname:
            other_commands.append(f"hostname {hostname}")
            print(f"Setting hostname to: {hostname}")
        if interface_vlan and ip_address and subnet_mask:
            other_commands.extend([
                f"vlan {interface_vlan}",
                f"interface vlan{interface_vlan}",
                f" ip address {ip_address} {subnet_mask}"
            ])
            print(f"Configuring interface VLAN{interface_vlan} with IP {ip_address}/{subnet_mask}")
        if default_gateway:
            other_commands.append(f"ip route 0.0.0.0 0.0.0.0 {default_gateway}")
            print(f"Setting default gateway to: {default_gateway}")

        if other_commands:
            configurep(other_commands)
            print("Applied device-specific configurations.")

        # Get mapping of switch IDs to serial numbers
        switch_id_to_serial = get_switch_id_serial_mapping()
        if not switch_id_to_serial:
            print("Error: Unable to obtain the mapping of switch IDs to serial numbers.")
            continue
        serial_to_switch_id = {v: k for k, v in switch_id_to_serial.items()}

        # Configure stacking
        if switches_data:
            for switch_config in switches_data:
                serial_number = switch_config.get('serial_number')
                stack_priority = switch_config.get('stack_priority')
                stack_number = switch_config.get('stack_number')
                if not (serial_number and stack_priority and stack_number):
                    print(f"Stack configuration parameters are missing for switch with serial number {serial_number}")
                    continue
                switch_id = serial_to_switch_id.get(serial_number)
                if switch_id:
                    stack_commands = [
                        f"switch {switch_id} priority {stack_priority}",
                        f"switch {switch_id} renumber {stack_number}"
                    ]
                    for cmd in stack_commands:
                        executep(cmd)
                    print(f"Successfully configured stacking settings for switch {switch_id} (Serial Number: {serial_number})")
                else:
                    print(f"Error: Unable to determine switch ID for serial number {serial_number}.")
        else:
            print("No stacking configuration provided.")

        # Check and handle version upgrade
        version_pat = r'\d+\.\d+\.\d+[a-zA-Z]?'
        current_version_match = re.search(rf"Cisco IOS XE Software, Version ({version_pat})", version_output)
        if version_upgrade:
            upgrade_version_match = re.search(rf'\.({version_pat})\.', version_upgrade)
        else:
            upgrade_version_match = None

        if current_version_match and upgrade_version_match:
            current_version = current_version_match.group(1).strip()
            upgrade_version = upgrade_version_match.group(1).strip()
            if current_version == upgrade_version:
                print("Current version matches the desired version; no upgrade needed.")
            else:
                print("Version mismatch detected; initiating upgrade process.")
                download_url = f"http://{ztp_server}/download/{version_upgrade}"
                local_file = f"/bootflash/guest-share/{version_upgrade}"

                # Download upgrade image
                download_cmd = f'curl -s -o {local_file} {download_url}'
                download_result = os.system(download_cmd)
                if download_result != 0:
                    print("Error: Failed to download the upgrade image.")
                    continue
                print("Upgrade image downloaded successfully.")

                # Deploy EEM scripts for upgrade and cleanup
                deploy_eem_script(
                    name='check_version',
                    event_pattern='syslog pattern ".*%SYS-5-RESTART.*" maxrun 100',
                    actions=[
                        'action 1.0 cli command "enable"',
                        'action 1.1 cli command "term length 0"',
                        'action 1.2 cli command "show version"',
                        'action 1.3 wait 30',
                        f'action 2.0 regexp "Cisco IOS XE Software, Version (\d+\.\d+\.\d+[a-zA-Z]?)" "$_cli_result" version',
                        'action 2.1 if $_regexp_result eq 1',
                        f'action 2.2 if $version ne "{upgrade_version}"',
                        'action 3.0 cli command "event manager run upgrade"',
                        'action 3.1 syslog msg "Version mismatch detected; upgrade initiated"',
                        'action 4.0 end',
                        'action 4.1 end'
                    ]
                )

                deploy_eem_script(
                    name='upgrade',
                    event_pattern='none maxrun 800',
                    actions=[
                        'action 1.0 cli command "enable"',
                        'action 1.1 cli command "term length 0"',
                        'action 1.2 cli command "write memory"',
                        f'action 2.0 cli command "install add file bootflash:guest-share/{version_upgrade} activate commit" pattern "y/n"',
                        'action 2.1 cli command "y"',
                        'action 3.0 syslog msg "System reload initiated"'
                    ]
                )

                deploy_eem_script(
                    name='cleanup',
                    event_pattern='syslog pattern ".*%SYS-5-RESTART.*" maxrun 100',
                    actions=[
                        'action 1.0 cli command "enable"',
                        'action 2.0 cli command "install remove inactive" pattern "y/n"',
                        'action 2.1 cli command "y"',
                        'action 3.0 syslog msg "Cleanup complete"'
                    ]
                )
        else:
            print("Current version matches the desired version; no upgrade required.")

    print("\n*** ZTP Day0 Python Script Execution Complete ***\n")

    # Save configuration and reload device
    executep('write memory')
    time.sleep(5)
    executep('reload')

if __name__ == "__main__":
    main()