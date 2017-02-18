# import logging
from netmiko import ConnectHandler
from datetime import datetime


juniper_srx = {
    'device_type': 'juniper',
    'ip':   '192.168.10.1',
    'username': 'jkennemer',
    'password': '*.l0broW@',
    'port': 22,               # there is a firewall performing NAT in front of this device
    'verbose': False
}

all_devices = [juniper_srx]


start_time = datetime.now()

for a_device in all_devices:
    net_connect = ConnectHandler(**a_device)
    output = net_connect.send_command("show configuration")
    print("\n\n>>>>>>>>> Device {0} <<<<<<<<<".format(a_device['device_type']))
    print(output)
    print(">>>>>>>>> End <<<<<<<<<")
    net_connect.disconnect()

end_time = datetime.now()

total_time = end_time - start_time

print(total_time)
