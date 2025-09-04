# Mercs AP client code

This holds all the code that communicates between the AP server and PCSX2 at
runtime. I've tried to divide it up sensibly.

## __init__.py

The entry point. This contains the client launching code and not much else.

## MercenariesClient.py

This contains the actual AP client. All code that communicates with the AP server
lives here. It is also responsible for creating the game state and game connector
and wiring them together.

This contains handlers that are invoked when messages are received from the host,
and handles id-to-item mapping and whatnot before forwarding the messages to the
game state.

## MercenariesConnector.py

The interface between the client and the IPC connector. Translates between the
IDs that the client uses and the data structures expected by the IPC library.

This is where yaml-dependent logic, like auto-release of missable checks or
intel threshold calculation, is implemented. It is also where the retry logic
for send failures when communicating with the game goes.

## MercenariesIPC.py

Game-specific memory wiggling lives here. This turns requests from the game state
("add a new shop unlock") into the specific sequence of memory reads and writes
needed to enact that.

### shop.py, shopdata.py, deck.py

Supporting libraries for `MercenariesIPC.py` containing lists of memory addresses,
struct layouts, etc.

## lua.py, lopcode.py

In-memory inspector for the Lua VM used by Mercenaries. Supports state traversal,
function decompilation, and limited editing of the live state.

## pine.py

Client library for the PINE remote debug protocol used by PCSX2. This is the
lowest-level component; all it can do is read and write emulator memory.

## util.py

Small shared utilities.
