import socket
import sys


HEADER_SIZE = 10


def receive_all(connection, size):
    data = b""
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Client disconnected")
        data += chunk
    return data


def receive_message(connection):
    header = receive_all(connection, HEADER_SIZE)
    size = int(header.decode())
    return receive_all(connection, size).decode()


def send_message(connection, message):
    data = message.encode()
    header = f"{len(data):0{HEADER_SIZE}}".encode()
    connection.sendall(header + data)


if len(sys.argv) != 2:
    print("Usage: python serv.py <port>")
    sys.exit(1)

port = int(sys.argv[1])
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", port))
server_socket.listen()

print(f"Server is listening on port {port}")

while True:
    connection, address = server_socket.accept()
    print(f"Connection from {address}")
    with connection:
        while True:
            try:
                command = receive_message(connection)
            except ConnectionError:
                break

            print(f"Request: {command}")
            if command.lower() == "quit":
                send_message(connection, "Goodbye!!")
                break
            send_message(connection, "ERR That command is not supported yet")