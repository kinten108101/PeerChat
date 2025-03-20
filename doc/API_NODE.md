Follows the communication protocol as specified in [[/docs/PROTOCOL.md]].

## (Node) Talks to a Node

From a Node, send a string to the other Node's IP address.

- `peer_connect:{ address: "$node_address" }`: Attempt to connect with a peer node. The peer node will return an ACK in the form of `result:{ status: "OK", token: "$token" }`

## Control a Node

If you're an interface program, you'd like to communicate with the node agent in order to control it. Each running node agent exposes a shmem region where it will receive (consume) a string message.

Write a string to `$app/_nodes/$node_adress.in`, where `$app` is the path to a local copy of this project repository on the machine, and `$node_adress` is the IP address of the node agent, in the form of `$inet6:$portnum`.

- `peer_connect:$peer_node_address`: Tells the node to perform a connection to a peer at the IP address `$peer_node_address`
- `submit_info`: Force the node to re-register itself with the tracker
- `exit`: Force the node to exit

Read the status / response of a node at `$app/_nodes/$node_address.out`. Make sure to fully consume / clear the region after reading.