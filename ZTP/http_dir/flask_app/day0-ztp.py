# 文件位置: /usr/local/cisco/ZTP/http_dir/flask_app

# 导入必要的模块
from cli import configure, cli, configurep, executep
import json
import os
import time
import subprocess
import re

def normalize_mac_address(mac_address):
    """将 MAC 地址规范化为小写并去除分隔符"""
    return mac_address.replace(":", "").replace(".", "").lower()

def extract_mac_from_show_version():
    """从 'show version' 输出中提取 Base Ethernet MAC Address"""
    version_result = cli('show version')
    mac_pattern = re.compile(r"Base Ethernet MAC Address\s+:\s+([0-9a-fA-F:]+)")
    match = mac_pattern.search(version_result)
    if match:
        return match.group(1).strip()
    return None

def get_switch_id_by_mac(normalized_mac):
    """通过规范化的 MAC 地址获取 switch id"""
    show_switch_output = cli('show switch').split('\n')

    for line in show_switch_output:
        match = re.search(r"([0-9a-fA-F:.]{12,17})", line)
        if match:
            line_mac = normalize_mac_address(match.group(1))
            if normalized_mac == line_mac:
                fields = line.split()
                if len(fields) >= 2:  # 确保 `fields` 列表中包含至少 2 个元素
                    switch_id = fields[0].strip().lstrip('*')  # 去掉可能存在的星号
                    if switch_id.isdigit():
                        return switch_id
    return None

def deploy_eem_upgrade_script(image):
    install_command = f'install add file bootflash:guest-share/{image} activate commit'
    eem_commands = [
        'event manager applet upgrade',
        'event none maxrun 800',
        'action 0010 cli command "enable"',
        'action 0011 cli command "term length 0"',
        'action 0012 cli command "write memory"',
        f'action 0020 cli command "{install_command}" pattern "y/n"',
        'action 0021 cli command "y"',
        'action 0030 syslog msg "reload of the system"'
    ]
    configurep(eem_commands)
    print('*** Successfully configured upgrade EEM script on device! ***')

def deploy_eem_cleanup_script():
    install_command = 'install remove inactive'
    eem_commands = [
        'event manager applet cleanup',
        'event syslog pattern ".*%SYS-5-RESTART.*" maxrun 100',
        'action 0010 cli command "enable"',
        f'action 0020 cli command "{install_command}" pattern "y/n"',
        'action 0021 cli command "y"',
        'action 0030 syslog msg "cleanup complete"'
    ]
    configurep(eem_commands)
    print('*** Successfully configured cleanup EEM script on device! ***')

def deploy_eem_check_version(version_upgrade):
    eem_commands = [
        'event manager applet check_version',
        'event syslog pattern ".*%SYS-5-RESTART.*" maxrun 100',
        'action 0010 cli command "enable"',
        'action 0011 cli command "term length 0"',
        'action 0012 cli command "show version"',
        'action 0013 wait 30',
        f'action 0020 regexp "Cisco IOS XE Software, Version ([0-9.]+)" $_cli_result version',
        'action 0021 if $_regexp_result eq 1',
        f'action 0022 if $version ne "{version_upgrade}"',
        'action 0030 cli command "event manager run upgrade"',
        'action 0031 syslog msg "version mismatch, upgrade initiated"',
        'action 0040 end',
        'action 0041 end'
    ]
    configurep(eem_commands)
    print('*** Successfully configured version check EEM script on device! ***')

def main():
    print("\n\n *** Sample ZTP Day0 Python Script *** \n\n")

    # 获取设备型号和序列号
    version_result = cli('show version')

    # 将输出按行分割成列表
    version_list = version_result.split('\n')

    # 初始化变量来存储系统序列号和型号
    model_number = ""
    device_sn = ""
    base_mac = extract_mac_from_show_version()

    # 遍历列表，查找包含 "Model Number" 和 "System Serial Number" 的行
    for x in version_list:
        if "Model Number" in x:
            try:
                model_number = x.split(":")[1].strip()
            except IndexError:
                print(f"Error: Could not extract model number from line: '{x}'")
        if "System Serial Number" in x:
            try:
                device_sn = x.split(":")[1].strip()
            except IndexError:
                print(f"Error: Could not extract serial number from line: '{x}'")

    # 确保提取到的 MAC 地址是完整且格式正确
    if not base_mac or not re.match(r'^[0-9a-fA-F:]{17}$', base_mac):
        print(f"Error: Extracted MAC address {base_mac} is not in the correct format.")
        return

    # 获取设备 IP 地址
    device_ip = ""
    if_result = cli('show ip interface brief').split('\n')
    for x in if_result:
        if 'DHCP' in x:
            device_ip = x.split()[1]

    # 配置设备主机名为型号加序列号
    if device_sn and model_number:
        hostname_init = f"{model_number}-{device_sn}"
        configurep([f"hostname {hostname_init}"])

        # 准备要发送的数据
        data = json.dumps({
            "model_number": model_number,
            "device_sn": device_sn,
            "device_ip": device_ip
        })

        # 使用 curl 命令发送 POST 请求
        yin = "'"  # 用于避免 SyntaxError
        result = os.popen(
            f'curl -X POST -H "Content-Type: application/json" -d {yin}{data}{yin} http://10.0.0.131/device_config_json')

        # 读取并解析响应
        response = json.loads(result.read())
        config_list = response.get('config')

        # 应用接收到的配置
        if config_list:
            configurep(config_list)

        # 获取设备特定的堆叠配置和版本升级信息
        stack_priority = response.get('stack_priority')
        stack_number = response.get('stack_number')
        hostname = response.get('hostname')
        version_upgrade = response.get('version_upgrade')
        interface_vlan = response.get('interface_vlan')
        ip_address = response.get('ip_address')
        subnet_mask = response.get('subnet_mask')
        default_gateway = response.get('default_gateway')

        # 配置 特殊配置
        if hostname or interface_vlan or ip_address or subnet_mask or default_gateway:
            other_commands = [
                f"hostname {hostname}",
                f"vlan {interface_vlan}",
                f"interface vlan{interface_vlan}\n ip address {ip_address} {subnet_mask}",
                f"ip route 0.0.0.0 0.0.0.0 {default_gateway}"
            ]
            configurep(other_commands)

        # 获取 switch id 并应用堆叠配置
        print("\n\n *** ZTP Day0 Python Script Stacking *** \n\n")
        if stack_priority and stack_number:
            normalized_mac = normalize_mac_address(base_mac)
            switch_id = get_switch_id_by_mac(normalized_mac)
            if switch_id:
                cli(f'switch {switch_id} priority {stack_priority}')
                cli(f'switch {switch_id} renumber {stack_number}')
            else:
                print(f"Error: Could not find switch id for MAC address {base_mac}")

    # 应用版本升级前检查当前版本
    print("\n\n *** ZTP Day0 Python Script Downloading *** \n\n")
    current_version_match = re.search(r"Cisco IOS XE Software, Version ([0-9.]+)", version_result)
    if current_version_match:
        current_version = current_version_match.group(1).strip()
        if current_version != version_upgrade:
            # 下载版本文件到交换机的 flash
            download_url = f'http://10.0.0.131/download/{version_upgrade}'
            local_file_guestshell = f'/bootflash/guest-share/{version_upgrade}'
            process = subprocess.Popen(['curl', '-o', local_file_guestshell, download_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(f"Error downloading image: {stderr.decode()}")
                return
            print("\n\n *** ZTP Day0 Python Script Downloading Complete *** \n\n")

    deploy_eem_check_version(version_upgrade)
    deploy_eem_upgrade_script(version_upgrade)
    deploy_eem_cleanup_script()
    time.sleep(5)
    executep('write memory')
    time.sleep(5)
    executep('reload')
    print("\n\n *** ZTP Day0 Python Script Execution Complete *** \n\n")

# 确保脚本作为主程序运行
if __name__ == "__main__":
    main()