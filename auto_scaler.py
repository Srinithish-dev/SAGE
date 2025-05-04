import docker
import time
import os
import subprocess
import re

client = docker.from_env()
container_base_name = "app"
base_port = 5001
max_cpu = 80.0
min_cpu = 15.0
idle_time = {}
scale_down_wait = 30 # seconds


def get_app_containers():
    return [c for c in client.containers.list() if container_base_name in c.name]


def get_next_port():
    used_ports = [int(c.attrs['HostConfig']['PortBindings']['5001/tcp'][0]['HostPort']) for c in get_app_containers()]
    port = base_port
    while str(port) in map(str, used_ports):
        port += 1
    return port


def update_nginx_config():
    containers = get_app_containers()

    gateway_ip = "172.17.0.1"  # Static Docker bridge IP for EC2/Linux
    server_lines = [
        f"server {gateway_ip}:{c.attrs['HostConfig']['PortBindings']['5001/tcp'][0]['HostPort']};"
        for c in containers
    ]

    with open("nginx.conf.template", "r") as f:
        template = f.read()
    config = template.replace("{{servers}}", "\n        ".join(server_lines))
    with open("nginx/default.conf", "w") as f:
        f.write(config)

    subprocess.run(["docker", "exec", "nginx", "nginx", "-s", "reload"])
    print("[*] NGINX config updated and reloaded")


def scale_up():
    port = get_next_port()
    name = f"{container_base_name}_{port}"
    print(f"[+] Spawning new container {name} on port {port}")
    client.containers.run(
        "sage",
        name=name,
        ports={"5001/tcp": port},
        environment={"FLASK_PORT": "5001"},
        detach=True
    )
    time.sleep(1)
    update_nginx_config()


def scale_down():
    containers = get_app_containers()
    if len(containers) <= 1:
        return

    now = time.time()
    for c in containers:
        name = c.name

        # Skip the default container
        if name == "app_5001":
            continue

        idle_start = idle_time.get(name)
        if idle_start and (now - idle_start >= scale_down_wait):
            print(f"[-] Removing container {name} after being idle for {scale_down_wait} seconds")
            c.stop()
            c.remove()
            idle_time.pop(name, None)
            update_nginx_config()
            break  # remove only one at a time


def monitor():
    while True:
        containers = get_app_containers()
        for c in containers:
            try:
                stats = c.stats(stream=False)

                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                num_cpus = len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [])) or 1
                online_cpus = stats['cpu_stats'].get('online_cpus', num_cpus)

                if system_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                else:
                    cpu_percent = 0.0

                print(f"{c.name}: CPU={cpu_percent:.2f}%")

                if cpu_percent > max_cpu:
                    idle_time.pop(c.name, None)
                    scale_up()

                elif cpu_percent < min_cpu:
                    if c.name not in idle_time:
                        idle_time[c.name] = time.time()
                else:
                    idle_time.pop(c.name, None)

            except Exception as e:
                print(f"Error reading {c.name}: {e}")

        scale_down()
        time.sleep(1)

                


if __name__ == '__main__':
    update_nginx_config()
    monitor()
