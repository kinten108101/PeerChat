# PeerChat

> Warning: This project is still WIP with new breaking API changes every day

PeerChat is minimal peer-to-peer messaging system and application. Host a platform of chatrooms for your group of friends or school community.

PeerChat is inspired by Discord, Matrix, etc.

## Installation

Requires python >= 3.12

To run the node program, create a `.node-agent.env`, then run the program with `python3 node-agent.py`.

To run the tracker program, create a `.tracker.env`, then run the program with `python3 tracker.py`.

Also in this repository is a sample GUI client implemention at `chat-ui`. To run this, make sure you have installed all dependencies, preferably in a Python virtual environment. You should have tkinter on your system, which comes prebundled with the Python binding which `chat-ui.py` needs. Other dependencies are listed in `requirements.txt`. Finally, change working directory to `chat-ui`, and execute `./chat-ui.py`

## Contribution

Please read all the documentation carefully at `doc` before contributing. This folder contains all information about the coding style and protocols we use.
