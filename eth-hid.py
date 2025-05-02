#!/usr/bin/env python3

import argparse
import socket
import time
from pprint import pprint


def server_sink_and_show_text(full_config, config_keys, context):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", context["port"]))
    sock.listen(1)
    while True:
        client, addr = sock.accept()
        print("Client %s connected" % str(addr))
        while True:
            data = client.recv(512).decode("utf-8")
            print(data)


def server_source_garbage_text(full_config, config_keys, context):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", context["port"]))
    sock.listen(1)
    while True:
        client, addr = sock.accept()
        print("Client %s connected" % str(addr))
        while True:
            client.send("Hello World!\n".encode("utf-8"))
            time.sleep(1)


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
