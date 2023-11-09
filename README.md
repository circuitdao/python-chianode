# About

Python-chianode is a Python wrapper for [Chia blockchain](https://www.chia.net) full node APIs.

The package supports the [standard RPC API](https://github.com/Chia-Network/chia-blockchain/blob/main/chia/rpc/full_node_rpc_client.py) of Chia full nodes running on localhost via the ```StandardClient```, as well as the [Mojonode API](https://api.mojonode.com/docs) via the derived ```MojoClient``` class.

Mojonode provides endpoints not available via the standard RPC interface, blockchain data via SQL query, and an event stream for blockchain and mempool events. Note that Mojonode does not implement all standard RPCs. The ```get_routes``` endpoint returns a list of available endpoints.

# Installation

To install python-chianode, run

```pip install python-chianode```

# Quick start

Import and instantiate the Chia node client in your Python file as follows

```
from chianode.mojoclient import MojoClient

node_client = MojoClient()
```

By default, ```MojoClient``` connects to Mojonode for both standard and non-standard endpoints. To use Mojonode in conjunction with a full node running on localhost for standard RPCs, do
```
from chianode.mojoclient import MojoClient
from chianode.constants import NodeProvider

node_client = MojoClient(standard_node_provider=NodeProvider.FULLNODE)
```

More detailed examples on how to use the wrapper can be found in ```example_rpc.py``` and ```example_events.py``` files.