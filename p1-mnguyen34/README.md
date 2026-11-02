# cpsc471-ftp
## CPSC 471-08 Programming Assignment 1

## Members/Emails:

### Martin Nguyen / martinnguyen34@csu.fullerton.edu
### Jasmine Cerasuolo / Jcerasuolo@csu.fullerton.edu
### Aijahlin Jallo-Jamboria / aijahlin@csu.fullerton.edu
### Nghi Vu / nghivu@csu.fullerton.edu

## Language: Python

## DESIGN: 
1.  **Message framing:** All messages start with a 10-byte header holding
   the payload length, padded with zeros (e.g. `0000000009`), followed by
   exactly that many bytes. `send()` and `recv()` may move fewer bytes than
   requested, so `send_all()` and `receive_all()` loop until every byte is moved.


## Special Notes: