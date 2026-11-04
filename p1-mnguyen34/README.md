# cpsc471-ftp
## CPSC 471-08 Programming Assignment 1

## Members/Emails:

### Martin Nguyen / martinnguyen34@csu.fullerton.edu
### Jasmine Cerasuolo / Jcerasuolo@csu.fullerton.edu
### Aijahlin Jallo-Jamboria / aijahlin@csu.fullerton.edu
### Nghi Vu / nghivu@csu.fullerton.edu

## Language: Python

## How to Run:
1. 

## DESIGN: 
1.  **Message framing:** All messages start with a 10-byte header holding the payload length, padded with zeros (e.g. `0000000009`), followed by exactly that many bytes. `send()` and `recv()` may move fewer bytes than requested, so `send_all()` and `receive_all()` loop until every byte is moved.

2. **Ephemeral Listener:** For each ls, get, and put, the client binds a new socket to port 0 so the OS assigns a free port, then sends that port
number to the server, which connects to it as the data connection.

3. **do_ls function:** The client opens an ephemeral listener and sends `ls <port>` on the control connection. If the server replies `OK`, it connects to that port and sends the directory listing (10-byte size header + listing) on the data connection. The client prints the listing and the number of bytes received, then closes the data connection. If the server replies `ERR`, the client prints the error and no data connection is used.

4. **do_get function:** The client opens an ephemeral listener and sends `get <filename> <port>`. The port is always the last word, so the server splits it off from the right, which lets file names contain spaces. If the file doesn't exist, the server replies `ERR` and no data connection is opened; the client prints the error. Otherwise the server replies `OK`, connects to the port, and sends the file (10-byte size header + file bytes). The client writes the file in binary mode, so any file type works, and prints `<filename> <bytes> bytes transferred`.

5. **do_put function:** The client first checks that the file exists locally; if not, it prints an error and never contacts the server. Otherwise it opens an ephemeral listener and sends `put <filename> <size> <port>`. The last two words are always the size and port, so the server splits them off from the right, which lets file names contain spaces. If the server replies `OK`, it connects to the port, and the client sends the file (10-byte size header + file bytes) in 64 KB chunks so large files don't have to fit in memory. After the data connection closes, the server sends a second reply on the control connection: `OK` once the whole file is saved, or `ERR` if it failed. The client waits for this reply before printing `<filename> <bytes> bytes transferred`, so the next command's reply isn't confused with it.


## Special Notes:

1. If 15 seconds pass without the server connecting to the ephemeral port, the client will time out, print an error, and return to ftp> prompt