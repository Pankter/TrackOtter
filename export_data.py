#! /usr/bin/python3
# import os 
import argparse
import platform
import psutil
import datetime
import prometheus_client
import json
import os
import sys

parser = argparse.ArgumentParser(
    description="reads in system information and exports them")
parser.add_argument("-v", "--verbose",  action="store_true",
                    help="verbose output")
# parser.add_argument("-c", "--config", type=str,
#                     help="Path to configuration file")
parser.add_argument("-d", "--dry-run", action="store_true", help="Performs a dry run without actually doing anything")
args = parser.parse_args()


def get_system_info():
    """Gathers system information using the platform module."""
    """See the official documentation"""
    info = {
        'System': platform.system(),
        'Node Name': platform.node(),
        'Release': platform.release(),
        'Version': platform.version(),
        'Machine': platform.machine(),
        'Processor': platform.processor(),
        'Architecture': platform.architecture(),
        'Python Version': platform.python_version(),
        'Users': psutil.users()
    }

    return info

def get_cpu_info():
    """Gathers information about the underlying CPU of the running system"""
    """See the official documentation"""
    cpu_info = {
      'CPU Count': psutil.cpu_count(logical=True), 
      'Acutal usable CPU': len(psutil.Process().cpu_affinity()), 
      'CPU Stats': psutil.cpu_stats(),
      # Return CPU frequency as a named tuple including current, min and max frequencies expressed in Mhz.
      'CPU Frequency': psutil.cpu_freq(percpu=True),
      # Return the average system load over the last 1, 5 and 15 minutes as a tuple.
      'CPU Load (in %)': [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
    }

    return cpu_info

def get_processes():
    """Get the list of all processes"""
    # Creates a dictonary of the following structure '{pid: {name, username}}'
    procs = {p.pid: p.info for p in psutil.process_iter(['name', 'username', 'open_files'])}

    return procs

def get_parent(procs):
    parents = {}

    pids = procs.keys()
    for p in pids:
        proc = psutil.Process(p)
        parent_p = proc.parent()
        parents[p] = parent_p

    return parents

def get_sensor_information():
    sensor_info = {
        'Fan Speed': psutil.sensors_fans(),
        'Battery': psutil.sensors_battery()
    }

    return sensor_info

def secs2hours(secs):
    mm, ss = divmod(secs, 60)
    hh, mm = divmod(mm, 60)
    return "%d:%02d:%02d" % (hh, mm, ss)

def convert_Bytes_to_MB(bytes):
    return bytes / (1024 * 1024)

def get_memory_info():
    memory_info = {
        'Swap': psutil.swap_memory(),
        'Virtual Memory': psutil.virtual_memory()
    }

    return memory_info

def get_disk_info():
    disk_info = {
        'Mounts': psutil.disk_partitions(),
        'Disk Usage(/)': psutil.disk_usage('/'),
        'Disk Usage(/home)': psutil.disk_usage('/home/bob/'),
        'I/O Counter': psutil.disk_io_counters()
    }

    return disk_info

def get_network():

    network_info = {
        'Network I/O Counter': psutil.net_io_counters(pernic=True),
        'Network Connection': psutil.net_connections(kind='inet')
    }

    return network_info

def print_system_info(info, information_tag):
    """Prints the gathered system information in a readable format."""
    print(information_tag)
    print("===================")
    for key, value in info.items():
        print(f"{key}: {value}")
    print("===================")

def create_data_directory():
    dir_path = "data"
    try:
        os.makedirs(dir_path, exist_ok=True)
        os.chmod(dir_path, 0o755)
        print("created data directory...")
    except FileExistsError as e:
        print(e)
        print("Directory already exists.")
        print("This directory will be created and all data will be exported to it.")
        print("Remove the old directory or move it to another place.")
        print("Exiting program...")
        sys.exit(1)
        
def export_as_json(data):
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def populate_dictionary(dictionaries):
    system_data = {}
    for d in dictionaries:
        system_data.update(d)

    return system_data


def main():
  print("Starting script...")
  print("Collecting data...\n")
  system_info = get_system_info()
  # print_system_info(system_info, "System Information:")
  cpu_info = get_cpu_info()
  # print_system_info(cpu_info, "CPU Information:")

  process_list = get_processes()
  # print_system_info(process_list, "Processes:")

  get_parent(process_list)
  # need to convert Process object iterable
  parents = get_parent(process_list)
  print_system_info(parents, "Parent Processes:")

  # Returns a dictionary with informations about various sensors
  sensors = get_sensor_information()
  battery = sensors['Battery']

  # Prints string formatted the battery status and the time left
  print("charge = %s%%, time left = %s" % (battery.percent, secs2hours(battery.secsleft)))
  # Print the time and date when the device was booted, equivalent to uptime
  print(datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"))

  memory = get_memory_info()
  swap = memory['Swap']
  swap = swap._asdict()
  # Better or just take the Bytes?
  for key in swap.keys():
    swap[key] = convert_Bytes_to_MB(swap[key])
  memory['Swap'] = swap
  
  virt_mem = memory['Virtual Memory']
  virt_mem = virt_mem._asdict()

  for key in virt_mem.keys():
    if key != 'percent':
        virt_mem[key] = convert_Bytes_to_MB(virt_mem[key])

  memory['Virtual Memory'] = virt_mem
  # print_system_info(memory, "Memory Information:")

  disk_info = get_disk_info()
  disk_mounts = disk_info['Mounts']
  # print_system_info(disk_usage, "Disk Information:")

  for k, v in enumerate(disk_mounts):
    disk_mounts[k] = dict(v._asdict())

  disk_usage = {i: d for i, d in enumerate(disk_mounts, start=1)}

  disk_usage_root = disk_info['Disk Usage(/)']
  disk_usage_root = disk_usage_root._asdict()
  for key in disk_usage_root.keys():
    if key != 'percent':
        disk_usage_root[key] = convert_Bytes_to_MB(disk_usage_root[key])

  disk_usage_home = disk_info['Disk Usage(/)']
  disk_usage_home = disk_usage_home._asdict()
  for key in disk_usage_home.keys():
    if key != 'percent':
        disk_usage_home[key] = convert_Bytes_to_MB(disk_usage_home[key])

  disk_usage_io = disk_info['I/O Counter']
  disk_usage_io = disk_usage_io._asdict()
  for key in disk_usage_io.keys():
    if key == 'read_bytes' or key =='write_bytes':
        disk_usage_io[key] = convert_Bytes_to_MB(disk_usage_io[key])


  disk_info['Mounts'] = disk_usage
  disk_info['Disk Usage(/)'] = disk_usage_root
  disk_info['Disk Usage(/home)'] = disk_usage_home
  disk_info['I/O Counter'] = disk_usage_io
  # print_system_info(disk_info, "Disk Information:")

  net_info = get_network()

  net_counter = net_info['Network I/O Counter']
  net_conn = net_info['Network Connection']

  net_counter = {k: v._asdict() for k, v in net_counter.items()}

  for key, item in net_counter.items():
    for subkey, value in item.items():
        if subkey == 'bytes_sent' or subkey =='bytes_recv':
          net_counter[key][subkey] = convert_Bytes_to_MB(net_counter[key][subkey])

  net_conn = {i: v._asdict() for i, v in enumerate(net_conn, start=1)}
  net_info['Network I/O Counter'] = net_counter
  net_info['Network Connection'] = net_conn
  # print_system_info(net_info, "Network Information:")

  data_list = [system_info, cpu_info, process_list, parents, memory, disk_info, net_info]
  system_data = populate_dictionary(data_list)

  print("Exporting data as JSON file...")
  create_data_directory()
  export_as_json(system_data)


if __name__ == "__main__":
        main()


