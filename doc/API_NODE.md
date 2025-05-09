Follows the communication protocol as specified in [[/docs/PROTOCOL.md]].

## (Tracker) Talks to a Node

- `check_alive:{}`: Ping if a node agent is running. The node agent must reply `is_alive:{}`.

## (Node) Talks to a Node

From a Node, send a string to the other Node's IP address.

- `send_message:{ "channel": "$user:$channel", "message": "$message" }`

## Control a Node

If you're an interface program, you'd like to communicate with the node agent in order to control it. Each running node agent exposes a shmem region where it will receive (consume) a string message.

Write a string to `var/node_agent-$portnum/in`, where `$portnum` is the port number of the node agent on the machine.

- `submit_info:{}`: Force the node to re-register itself with the tracker
- `exit:{}`: Force the node to exit
- `login:{ "name": "$name", "password": "$password" }`: Authenticate as a user

Read the status / response of a node at `var/node_agent-$portnum/out`. Make sure to fully consume / clear the region after reading.
