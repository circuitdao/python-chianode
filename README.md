# About

Python-chianode is a Python wrapper for [Chia blockchain](https://www.chia.net) full node APIs.

The package supports the [official RPC API](https://docs.chia.net/full-node-rpc) for Chia nodes running on localhost, as well as the [Mojonode API](https://api.mojonode.com/docs). Calls are made asynchronously, and it is possible to receive streaming responses.

Mojonode provides advanced REST calls not available via the official RPC interface, blockchain data via SQL query, and an event stream for blockchain and mempool events. Note that Mojonode does not implement all official RPCs. The ```get_routes``` endpoint returns a list of available endpoints.

# Installation

To install python-chianode, run

```pip install python-chianode```

# Quick start

Import and instantiate the Chia node client in your Python file as follows

```
from chianode.mojoclient import MojoClient

node = MojoClient()
```

By default, both MojoClient and RpcClient connect to Mojonode. To connect to a local node only, do
```
from chianode.rpcclient import RpcClient
from chianode.constants import LOCALHOST

node = RpcClient(base_url=LOCALHOST)
```

To use Mojonode in conjunction with a local node, do
```
from chianode.mojoclient import MojoClient
from chianode.constants import LOCALHOST

node = MojoClient(base_url=LOCALHOST)
```

More detailed examples on how to use the wrapper can be found in ```example_rpc.py``` and ```example_events.py``` files.