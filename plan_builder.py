import openstack, os, sys

UUID = sys.argv[1]

conn = openstack.connect()
server = conn.compute.get_server(UUID)

template = ''


# Create server
flavor_d = server.flavor
flavor_name = flavor_d["original_name"]
flavor_id = conn.get_flavor(flavor_name)["id"]
key_name = server.key_name
project = server.project_id
server_name =  server.name

template = template + 'resource "openstack_compute_instance_v2" "' + server_name + '" {\n'
template = template + '  name = "' + str(server_name) +'"\n'
template = template + '  flavor_id = "' + str(flavor_id) + '"\n'
template = template + '  key_pair = "' + str(key_name) +'"\n'
template = template + '  stop_before_destroy = true\n\n'

# Network ports
floating_ip = ''
addrs = server.addresses
for addr in addrs.values():
    for a in addr:
        print(a)
        if a["OS-EXT-IPS:type"] == "fixed":
            fixed_ip = a["addr"]
            print(fixed_ip)
            for port in conn.list_ports():
                if port.fixed_ips[0]["ip_address"] == fixed_ip:
                    fixed_port_id = port.id
    try:
        if a["OS-EXT-IPS:type"] == "floating":
            floating_ip = a["addr"]
            floating_ip_port = conn.get_floating_ip(floating_ip)
            print(floating_ip_port)
    except:
       # nothing better than silent failures
        pass

template = template + '  network {\n    port = "' + fixed_port_id + '"\n  }\n\n'
print(floating_ip)
if floating_ip:
    template = template + '# Attach floating IP\n'
    template = template + '  network {\n    port = "' + floating_ip_port.id + '"\n\n'

# Block devices
blocks = server.attached_volumes

template = template + "#Attach block devices\n\n"
template = template + "#Attach OS device\n"
boot_index = 0
for block in blocks:
    template = template + '  block_device {\n    uuid = "' + block.id + '"\n'
    template = template + '    source_type = "volume"\n'
    template = template + '    destination_type = "volume"\n'
    template = template + '    boot_index = ' + str(boot_index) + '\n'
    template = template + '    delete_on_termination = false\n  }\n'
    boot_index = boot_index + 1

template = template + "}"

# Write the file in project_name directory
for project in conn.list_projects():
    if project.id == server.project_id:
        try:
            os.mkdir(project.name)
        except:
            pass
        break

f_out = open(project.name + "/" + server_name + ".tf", "w")
f_out.write(template)
f_out.close()
