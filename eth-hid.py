#!/usr/bin/env python3

import argparse
import socket
import time

parser = argparse.ArgumentParser()
parser.add_argument(
        "mode",
        nargs="?",
        help="The first argument selects the mode, advertise or interact"
)
parser.add_argument(
        "media_type",
        nargs="?",
        help="The second argument selects the media type, text only right now"
)
parser.add_argument(
        "direction",
        nargs="?",
        help="The third argument selects the direction, source or sink"
)
args = parser.parse_args()


def server_sink_and_show_text(mode, media_type, direction, details):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", details["port"]))
    sock.listen(1)
    while True:
        client, addr = sock.accept()
        print("Client %s connected" % str(addr))
        while True:
            data = client.recv(512).decode("utf-8")
            print(data)


def server_source_garbage_text(mode, media_type, direction, details):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", details["port"]))
    sock.listen(1)
    while True:
        client, addr = sock.accept()
        print("Client %s connected" % str(addr))
        while True:
            client.send("Hello World!\n".encode("utf-8"))
            time.sleep(1)


def client_show_text(mode, media_type, direction, details):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", details["port"]))
    while True:
        print(sock.recv(512).decode("utf-8"))


def client_transmit_input(mode, media_type, direction, details):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", details["port"]))
    while True:
        sock.send(input("").encode("utf-8"))


configuration = {
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


if not args.mode or args.mode not in configuration:
    if args.mode:
        print("invalid mode: %s" % args.mode)
    print("available modes:", ", ".join(configuration.keys()))
    exit(1)

if not args.media_type or args.media_type not in configuration[args.mode]:
    if args.media_type:
        print("invalid media_type: %s" % args.media_type)
    print("available modes:", ", ".join(configuration[args.mode].keys()))
    exit(1)

if args.direction not in configuration[args.mode][args.media_type]:
    if args.direction:
        print("invalid direction: %s" % args.direction)
    keys = configuration[args.mode][args.media_type].keys()
    print("available modes:", ", ".join(keys))
    exit(1)

handler = configuration[args.mode][args.media_type][args.direction]["activate"]
context = configuration[args.mode][args.media_type][args.direction]
handler(args.mode, args.media_type, args.direction, context)
