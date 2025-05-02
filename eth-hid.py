#!/usr/bin/env python3

import argparse
import socket
import time
from pprint import pprint
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, IPVersion
from zeroconf import ServiceInfo


# comp2 (or comp^2) is short for COMPosable COMPuting
# This service name is used for all services regardless of actual transport.
# Additional details and real transport are carried in the properties.
service_name = "_comp2._tcp.local."


def advertise_service(content, transport, direction, port):
    info = ServiceInfo(
        service_name,
        service_name,
        addresses=[socket.inet_aton("127.0.0.1")],
        port=port,
        properties={
            "content": content,
            "transport": transport,
            "direction": direction,
            "port": port
            },
        )
    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    zeroconf.register_service(info)
    return zeroconf, info


def unadvertise_service(zeroconf, info):
    zeroconf.unregister_service(info)
    zeroconf.close()


def scan_for_targets(full_config, config_keys, context):
    zeroconf = Zeroconf()
    connection_options = []

    class MyListener(ServiceListener):

        def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            print(f"Service {name} updated")

        def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            print(f"Service {name} removed")

        def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            info = zc.get_service_info(type_, name)
            print(f"Service {name} added, service info: {info}")
            connection_options.append(info)

    listener = MyListener()
    browser = ServiceBrowser(zeroconf, service_name, listener)
    try:
        while True:
            query = input("Press enter to get list of options\n").rstrip()
            if query == "quit" or query == "q":
                break
            if query == "":
                print("Available options (also, 'quit'):")
                for i, opt in enumerate(connection_options):
                    print(f"{i}: {opt.properties}")
                continue
            index = int(query)
            if index < 0 or index >= len(connection_options):
                print("bad selection")
                continue
            print(f"option {index} selected: {connection_options[index]}")
            properties = connection_options[index].properties
            decoded_props = {}
            for key, value in properties.items():
                decoded_props[key.decode("utf-8")] = value.decode("utf-8")
            print(decoded_props)
            content = decoded_props["content"]
            remote_direction = decoded_props["direction"]
            local_direction = "sink"
            if remote_direction == "sink":
                local_direction = "source"
            keys = ["interact", content, local_direction]
            traverse_config(keys)
    finally:
        zeroconf.close()


def server_sink_and_show_text(full_config, config_keys, context):
    port = context["port"]
    zeroconf, info = advertise_service("text", "tcp", "sink", port)
    print("Advertising started, listening")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(1)
    try:
        while True:
            client, addr = sock.accept()
            print("Client %s connected" % str(addr))
            while True:
                data = client.recv(512).decode("utf-8")
                print(data)
    except KeyboardInterrupt:
        unadvertise_service(zeroconf, info)


def server_source_garbage_text(full_config, config_keys, context):
    port = context["port"]
    zeroconf, info = advertise_service("text", "tcp", "source", port)
    print("Advertising started, listening")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(1)
    try:
        while True:
            client, addr = sock.accept()
            print("Client %s connected" % str(addr))
            while True:
                client.send("Hello World!\n".encode("utf-8"))
                time.sleep(1)
    except KeyboardInterrupt:
        unadvertise_service(zeroconf, info)


def client_show_text(full_config, config_keys, context):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", context["port"]))
    while True:
        print(sock.recv(512).decode("utf-8"))


def client_transmit_input(full_config, config_keys, context):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", context["port"]))
    while True:
        sock.send(input("").encode("utf-8"))


def print_config(full_config, config_keys, context):
    print("Configuration:")
    pprint(full_config)


configuration = {
    "show_config": {
        "activate": print_config
    },
    "scan": {
        "activate": scan_for_targets
    },
    "advertise": {
        "text": {
            "source": {
                "transport": "tcp",
                "port": 2787,
                "activate": server_source_garbage_text
            },
            "sink": {
                "transport": "tcp",
                "port": 2787,
                "activate": server_sink_and_show_text
            }
        }
    },
    "interact": {
        "text": {
            "source": {
                "transport": "tcp",
                "port": 2787,
                "activate": client_transmit_input
            },
            "sink": {
                "transport": "tcp",
                "port": 2787,
                "activate": client_show_text
            }
        }
    }
}


def traverse_config(keys):
    context = configuration
    for config_key in keys:
        if config_key not in context:
            print("invalid key: %s" % config_key)
            print("available keys at this level:", ", ".join(context.keys()))
            exit(1)
        context = context[config_key]

    # now at the end of the specified key traversal
    if "activate" not in context:
        print("incomplete configuration traversal: %s" % keys)
        print("available keys at this level:", ", ".join(context.keys()))
        exit(1)

    handler = context["activate"]
    handler(configuration, keys, context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "config_keys",
            nargs="*",
            help="Each positional argument traverses into the config tree"
    )
    args = parser.parse_args()

    traverse_config(args.config_keys)
