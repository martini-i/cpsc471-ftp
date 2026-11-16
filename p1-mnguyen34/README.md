# cpsc471-ftp
## CPSC 471-08 Programming Assignment 1

## Members/Emails:

### Martin Nguyen / martinnguyen34@csu.fullerton.edu
### Jasmine Cerasuolo / Jcerasuolo@csu.fullerton.edu
### Aijahlin Jallo-Jamboria / aijahlin@csu.fullerton.edu
### Nghi Vu / nghivu@csu.fullerton.edu

## Language: Python 3

## How to Run:
1. **Start the server** from the folder whose files it should share (uploaded files are saved there too):

       python3 serv.py <PORT>

   Example: `python3 serv.py 1234`

2. **Start the client** in another terminal or on another machine (downloaded files are saved in the client's current folder):

       python3 cli.py <SERVER MACHINE> <SERVER PORT>

   Example (same machine): `python3 cli.py localhost 1234`

3. **Enter commands at the `ftp>` prompt:**

       ftp> ls                 list files on the server
       ftp> get <filename>     download a file from the server
       ftp> put <filename>     upload a file to the server
       ftp> quit               disconnect and exit

   After each `get` or `put`, the client prints the file name and the number of bytes transferred.

4. **Stop the server** with `Ctrl+C`.


## DESIGN:

### Client design:
1.  **Message framing:** All messages start with a 10-byte header holding the payload length, padded with zeros (e.g. `0000000009`), followed by exactly that many bytes. `send()` and `recv()` may move fewer bytes than requested, so `send_all()` and `receive_all()` loop until every byte is moved.

2. **Ephemeral Listener:** For each ls, get, and put, the client binds a new socket to port 0 so the OS assigns a free port, then sends that port
number to the server, which connects to it as the data connection.

3. **do_ls function:** The client opens an ephemeral listener and sends `ls <port>` on the control connection. The server creates a sorted listing with one name per line, connects to the supplied port, and replies `OK` on the control connection. It then sends a 10-byte size header followed by the UTF-8 listing on the data connection. The client prints the listing and the number of bytes received, then closes the data connection. If the server replies `ERR`, the client prints the error and no data connection is used.

4. **do_get function:** The client opens an ephemeral listener and sends `get <filename> <port>`. The port is always the last word, so the server splits it off from the right, which lets file names contain spaces. If the file doesn't exist, the server replies `ERR` and no data connection is opened; the client prints the error. Otherwise the server replies `OK`, connects to the port, and sends the file (10-byte size header + file bytes). The client writes the file in binary mode, so any file type works, and prints `<filename> <bytes> bytes transferred`.

5. **do_put function:** The client first checks that the file exists locally; if not, it prints an error and never contacts the server. Otherwise it opens an ephemeral listener and sends `put <filename> <size> <port>`. The last two words are always the size and port, so the server splits them off from the right, which lets file names contain spaces. The server connects to the port and replies OK, then the client sends the file (10-byte size header + file bytes) in 64 KB chunks so large files don't have to fit in memory. After the data connection closes, the server sends a second reply on the control connection: `OK` once the whole file is saved, or `ERR` if it failed. The client waits for this reply before printing `<filename> <bytes> bytes transferred`, so the next command's reply isn't confused with it.

6. **quit:** The client sends `quit`, waits for the server's reply, then both sides close the control connection. The server stays running for the next client.

### Server Design:
1. Server Setup and Control Connection: The server starts by creating a TCP socket, binding it to the port specified by the user, and listening for incoming connections. When a client connects, the server accepts the connection and keeps the control channel open to receive multiple FTP commands. The server processes commands until the client sends quit or disconnects.

2. Command Processing: The server uses a 10-byte header to determine the length of each incoming command. It reads the specified number of bytes before processing the request. The server identifies the command (ls, get, put, or quit) and extracts any required arguments, such as filenames, file sizes, and data port numbers.

3. Data Connection: For every ls, get, or put command, the client creates a temporary listening socket using an ephemeral port. The client sends the port number through the control connection. The server then creates a separate TCP socket and connects to the client's temporary port. This connection is used only for the requested data transfer and is closed afterward.

4. GET Command: When the server receives get <filename> <port>, it checks whether the requested file exists and can be opened. If successful, the server connects to the client's data port and sends an OK response through the control connection. It then sends a 10-byte file-size header followed by the file contents in chunks of up to 65,536 bytes. If the file cannot be opened, the server sends an error response.

5. PUT Command: When the server receives put <filename> <size> <port>, it establishes the data connection and opens the destination file for writing. The server sends an initial OK response, receives the 10-byte file-size header, and verifies that it matches the expected size. It then receives the file in chunks and writes the data to disk. After successfully receiving the entire file, the server sends a final OK response through the control connection.

6. LS Command: When the server receives ls <port>, it retrieves the filenames from its current directory and sorts them alphabetically. It connects to the client's data port, sends OK through the control connection, and transfers the directory listing with a 10-byte length header. The data connection closes after the listing has been sent.

7. Error Handling and Session Termination: The server sends ERR responses when it encounters invalid commands or certain file and connection errors. It also prints success or failure messages in its terminal. When the client sends quit, the server sends a goodbye response and closes that client's control connection. The server continues running so that another client can connect.


## Special Notes:

1. If 15 seconds pass without the server connecting to the ephemeral port, the client will time out, print an error, and return to ftp> prompt
2. **Error handling:** A missing file, a missing local file, or an unknown command prints an error and the session continues. If the server drops the connection, the client prints an error and exits cleanly instead of crashing.
3. **End of input:** Pressing `Ctrl+D` at the prompt is treated as `quit`.
