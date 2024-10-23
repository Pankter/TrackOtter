#! /usr/bin/python3
# import os 
import argparse
import platform
import psutil
import datetime

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
    # process_list = psutil.process_iter()
    # process = {}

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

def print_system_info(info):
    """Prints the gathered system information in a readable format."""
    print("System Information:")
    print("===================")
    for key, value in info.items():
        print(f"{key}: {value}")

def main():
  print("Starting script...")
  print("Collecting data...\n")
  system_info = get_system_info()
  print_system_info(system_info)
  cpu_info = get_cpu_info()
  print_system_info(cpu_info)

  process_list = get_processes()
  print(process_list)

  get_parent(process_list)
  parents = get_parent(process_list)
  print(parents)

  # Returns a dictionary with informations about various sensors
  sensors = get_sensor_information()
  battery = sensors['Battery']
  # Prints string formatted the battery status and the time left
  print("charge = %s%%, time left = %s" % (battery.percent, secs2hours(battery.secsleft)))
  # Print the time and date when the device was booted
  print(datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"))

  memory = get_memory_info()
  swap = memory['Swap']
  swap = swap._asdict()
  swap['total'] = convert_Bytes_to_MB(swap['total'])
  swap['free'] = convert_Bytes_to_MB(swap['free'])

  print(memory['Swap'])
  print(swap['total'], swap['free'])
  # print(memory['Virtual Memory'])

if __name__ == "__main__":
        main()


