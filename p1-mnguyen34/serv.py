import socket
import sys
import os


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
                print("SUCCESS quit", flush=True)
                break

            parts = command.split(maxsplit=1)
            action = ""
            arguments = ""
            if len(parts) > 0:
                action = parts[0].lower()
            if len(parts) == 2:
                arguments = parts[1]
            transfer_started = False

            try:
                if action == "get" and arguments:
                    # port comes after the last space
                    last_space = arguments.rfind(" ")
                    if last_space == -1:
                        raise ValueError("Missing filename or data port")
                    filename = arguments[:last_space]
                    data_port = int(arguments[last_space + 1:])
                    size = os.path.getsize(filename)
                    with open(filename, "rb") as file:
                        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        try:
                            data_socket.settimeout(15)
                            data_socket.connect((address[0], data_port))
                            send_message(connection, "OK")
                            transfer_started = True
                            data_socket.sendall(f"{size:0{HEADER_SIZE}}".encode())
                            remaining = size
                            while remaining:
                                chunk = file.read(min(65536, remaining))
                                if not chunk:
                                    raise ConnectionError("File ended before all bytes were sent")
                                data_socket.sendall(chunk)
                                remaining -= len(chunk)
                        finally:
                            data_socket.close()
                    print(f"SUCCESS get {filename}: {size} bytes", flush=True)

                elif action == "put" and arguments:
                    # separate the port from the rest of the request
                    last_space = arguments.rfind(" ")
                    if last_space == -1:
                        raise ValueError("Missing filename, size, or data port")
                    data_port = int(arguments[last_space + 1:])
                    filename_and_size = arguments[:last_space]

                    # separate the size from the filename
                    last_space = filename_and_size.rfind(" ")
                    if last_space == -1:
                        raise ValueError("Missing filename or file size")
                    filename = filename_and_size[:last_space]
                    expected_size = int(filename_and_size[last_space + 1:])
                    if expected_size < 0:
                        raise ValueError("Invalid file size")
                    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        data_socket.settimeout(15)
                        data_socket.connect((address[0], data_port))
                        with open(filename, "wb") as file:
                            send_message(connection, "OK")
                            transfer_started = True
                            size = int(receive_all(data_socket, HEADER_SIZE).decode())
                            if size != expected_size:
                                raise ValueError("File size doesn't match put command")
                            remaining = size
                            while remaining:
                                chunk = data_socket.recv(min(65536, remaining))
                                if not chunk:
                                    raise ConnectionError("Upload ended before all bytes arrived")
                                file.write(chunk)
                                remaining -= len(chunk)
                    finally:
                        data_socket.close()
                    send_message(connection, "OK")
                    print(f"SUCCESS put {filename}: {size} bytes", flush=True)

                elif action == "ls":
                    data_port = int(arguments)
                    filenames = os.listdir(".")
                    filenames.sort()
                    listing_text = ""
                    for filename in filenames:
                        listing_text += filename + "\n"
                    listing = listing_text.encode()

                    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        data_socket.settimeout(15)
                        data_socket.connect((address[0], data_port))
                        send_message(connection, "OK")
                        transfer_started = True
                        data_socket.sendall(f"{len(listing):0{HEADER_SIZE}}".encode())
                        data_socket.sendall(listing)
                    finally:
                        data_socket.close()
                    print(f"SUCCESS ls: {len(listing)} bytes", flush=True)

                else:
                    send_message(connection, "ERR Unknown command or missing arguments")
                    print(f"FAILURE {action}: invalid command", flush=True)

            except (OSError, ValueError) as error:
                print(f"FAILURE {action}: {error}", flush=True)
                # get/ls have no final control reply
                if action in ("get", "ls") and transfer_started:
                    break
                try:
                    send_message(connection, f"ERR {error}")
                except OSError:
                    break