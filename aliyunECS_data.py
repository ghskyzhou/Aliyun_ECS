import psutil
import json
from flask import Flask, jsonify

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

config_info = read_json_file('monitor_config.json')

app = Flask(__name__)

def print_memory_info():
    memory_info = psutil.virtual_memory()
    res = f"{memory_info.used / (1024 ** 3):.2f} GB / {memory_info.total / (1024 ** 3):.2f} GB , {memory_info.percent}%"
    return res
    #print(res)
    #print(f"内存使用情况: {memory_info.used / (1024 ** 3):.2f} GB / {memory_info.total / (1024 ** 3):.2f} GB , {memory_info.percent}%")

def print_disk_info():
    partitions = psutil.disk_partitions()
    res = []
    #print("硬盘使用情况:")
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        res.append(f"{partition.device} 盘使用情况: {usage.used / (1024 ** 3):.2f} GB / {usage.total / (1024 ** 3):.2f} GB, {usage.percent}%")
        #print(f"{partition.device} 盘使用情况: {usage.used / (1024 ** 3):.2f} GB / {usage.total / (1024 ** 3):.2f} GB, {usage.percent}%")
    return res

def print_cpu_info():
    cpu_percent_total = psutil.cpu_percent(interval = 1)
    return f"{cpu_percent_total}%"

@app.route("/", methods = ['GET'])
def index():
    res = "{ \"CPU\": \"" + str(print_cpu_info()) + "\", \"Disk\": " + str(print_disk_info()) + ", \"Memory\": \"" + str(print_memory_info()) + "\"}"
    #print(res)
    return res.replace("'", '"')

if __name__ == '__main__': 
    print_disk_info()
    print_memory_info()
    app.run(host = config_info.get('host'), port = config_info.get('port'))