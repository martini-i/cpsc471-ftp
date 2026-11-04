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

def open_ephemeral_listener():
    # opens a listener socket on an ephemeral port and returns the socket and port number
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('', 0))
    listener.listen(1)
    listener.settimeout(15)
    return listener, listener.getsockname()[1]

def do_ls(control_sock):
    # send ls command to server and print reply
    listener, port = open_ephemeral_listener()
    send_command(control_sock, f"ls {port}")

    reply = receive_reply(control_sock)
    if not reply.startswith("OK"):
        print(reply)
        listener.close()
        return

    data_sock, _ = listener.accept()
    size = int(receive_all(data_sock, HEADER_SIZE).decode())
    listing = receive_all(data_sock, size)
    data_sock.close()
    listener.close()

    print(listing.decode(errors='replace'), end='')
    print(f"ls {size} bytes received")

def do_get(control_sock, filename):
    # send get command to server and print reply
    listener, port = open_ephemeral_listener()
    send_command(control_sock, f"get {filename} {port}")

    reply = receive_reply(control_sock)
    if not reply.startswith("OK"):
        print(reply)
        listener.close()
        return

    data_sock, _ = listener.accept()
    size = int(receive_all(data_sock, HEADER_SIZE).decode())
    file_data = receive_all(data_sock, size)
    data_sock.close()
    listener.close()

    with open(filename, 'wb') as f:
        f.write(file_data)

    print(f"{filename} {size} bytes transferred")

def do_put(control_sock, filename):
    # send put command to server and print reply
    if not os.path.isfile(filename):
        print(f"Error: {filename} does not exist or is not a file")
        return

    size = os.path.getsize(filename)
    listener, port = open_ephemeral_listener()
    send_command(control_sock, f"put {filename} {size} {port}")

    reply = receive_reply(control_sock)
    if not reply.startswith("OK"):
        print(reply)
        listener.close()
        return

    data_sock, _ = listener.accept()
    send_all(data_sock, f"{size:0{HEADER_SIZE}}".encode())
    with open(filename, 'rb') as f:
        while chunk := f.read(65536):
        # read file in chunks of 64KB to avoid loading entire file into memory
            send_all(data_sock, chunk)
    data_sock.close()
    listener.close()

    final_reply = receive_reply(control_sock)
    if final_reply.startswith("OK"):
        print(f"{filename} {size} bytes transferred")
    else:
        print(final_reply)

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <server_ip> <server_port>")
        sys.exit(1)
    server_name = sys.argv[1]
    server_port = int(sys.argv[2])

    control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        control_sock.connect((server_name, server_port))
    except Exception as e:
        print(f"Error connecting to server {server_name}:{server_port} ({e})")
        sys.exit(1)
    print(f"Connected to server {server_name}:{server_port}")

    while True:
        try:
            line = input("ftp> ").strip()
        except EOFError:
            line = "quit"
        if not line:
            continue

        parts = line.split(maxsplit=1)
        command = parts[0].lower()

        try:
            if command == "ls" and len(parts) == 1:
                do_ls(control_sock)
            elif command == "get" and len(parts) == 2:
                do_get(control_sock, parts[1])
            elif command == "put" and len(parts) == 2:
                do_put(control_sock, parts[1])
            elif command == "quit":

                send_command(control_sock, "quit")
                receive_reply(control_sock)
                control_sock.close()
                print("Goodbye")
                break
            else:
                print("Usage: ls | get <filename> | put <filename> | quit")

        except socket.timeout:
            print("Error: Connection timed out")

        except (RuntimeError, ConnectionError) as e:
            print(f"Error: Lost connection to server: ({e})")
            control_sock.close()
            break
            

if __name__ == "__main__":
    main()