import socket
import sys
import os

HEADER_SIZE = 10

def send_all(sock, data:bytes):
    # loops until all data is sent
    bytes_sent = 0
    while bytes_sent < len(data):
        sent = sock.send(data[bytes_sent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        bytes_sent += sent

def receive_all(sock, num_bytes:int):
    # loops until all num_bytes are received
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            raise RuntimeError("socket connection broken")
        data += chunk
    return data

def receive_reply(sock):
    # read one reply from server; 10-byte sized header then rest of msg
    header = receive_all(sock, HEADER_SIZE)
    size = int(header.decode())
    return receive_all(sock, size).decode()

def send_command(sock, text: str):
    # send one command to server; 10-byte sized header then rest of msg
    data = text.encode()
    send_all(sock, f"{len(data):0{HEADER_SIZE}}".encode() + data)
