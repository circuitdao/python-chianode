# About

Python-chianode is a Python wrapper for [Chia blockchain](https://www.chia.net) node APIs.

The package supports the [official RPC call API](https://docs.chia.net/full-node-rpc) for Chia nodes running on localhost, as well as the [Mojonode API](https://api.mojonode.com/docs).

Mojonode provides blockchain data via SQL query, an event stream for blockchain and mempool, and advanced REST calls not available via the official RPC interface.

# Installation

To install python-chianode, run

```pip install python-chianode```

# Quick start

Import the Chia node client in your Python file as follows

```from chianode.mojoclient import MojoClient```

or, if you are only interested in the official RPC interface,

```from chianode.rpcclient import RpcClient```

Examples are provided in the ```examples/``` directory.