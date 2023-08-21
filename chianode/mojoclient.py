import logging
import httpx
import uuid
import json
from datetime import datetime
from .rpcclient import RpcClient
from .constants import NEWLINE, GET, POST, MAINNET, LOCALHOST, MOJONODE, MOJONODE_RPC_ENDPOINTS


logging.getLogger(__name__).addHandler(logging.NullHandler())

    
class MojoClient(RpcClient):

    def __init__(self, base_url=MOJONODE, network=MAINNET, mojo_timeout=10, rpc_timeout=5): # 5 second timeout is the httpx default
        """Initialize a MojoClient instance.

        Keywork arguments:
        base_url -- the URL (exluding endpoint) for RPCs
        network -- the network to query
        mojo_timeout -- timeout in seconds for requests to Mojonode
        rpc_timeout -- timeout in seconds for RPCs
        """

        if base_url == MOJONODE: rpc_timeout = mojo_timeout # Override RPC timeout if Mojonode used for RPC calls
        RpcClient.__init__(self, base_url=base_url, network=MAINNET, timeout=rpc_timeout)
        
        self.mojo_headers = {"accept": "application/json", "Content-Type": "application/json"}
        self.mojo_timeout = mojo_timeout

        self._streams = {}

        self.mojonode_nonrpc_endpoints = [
            "/get_tx_by_name",
            "/get_uncurried_coin_spend",
            "/get_transactions_for_coin",
            "/get_query_schema",
            "/query",
            "/events",
            "/get_latest_singleton_spend"
        ]
        
        if self.base_url == MOJONODE:
            self.mojoclient = self.client
        else:
            self.mojoclient = httpx.AsyncClient(base_url=MOJONODE, http2=True, timeout=self.mojo_timeout)

            
    async def _mojo_request(self, method, endpoint, params, no_network=False):
        """Send a REST request to Mojonode.

        Keyword arguments:
        method -- a REST method (GET, POST, etc)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters
        no_network -- boolean indicating whether to add a network field to params
        """

        url = MOJONODE + endpoint
        data = json.dumps(self._add_network_param(params, no_network))

        if method == POST:
            logging.info(f"Sending POST request{NEWLINE}  URL: {url}{NEWLINE}  data: {data}")
            response = await self.mojoclient.post(url, content=data, headers=self.mojo_headers)
        else:
            raise ValueError(f"Unsupported REST method {method}")

        return response

    
    async def _mojo_request_no_network(self, method, endpoint, params):
        """Send a REST request to Mojonode without specifying a network

        Keyword arguments:
        method -- a REST method (GET, POST, etc)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters
        """

        return await self._mojo_request(method, endpoint, params, no_network=True)


    async def get_tx_by_name(self, tx_id):
        """Transaction by transaction ID.

        Arguments:
        tx_id -- a spend bundle name

        Returns the transaction (spend bundle) corresponding to the transaction ID (spend bundle name).
        Since spend bundles are mempool objects, Mojonode may occasionally fail to record a spend, resulting in missing data.
        """

        params = {"name": tx_id}
        return await self._mojo_request(POST, "get_tx_by_name", params)

    
    async def get_uncurried_coin_spend(self, coin_id):
        """Uncurried coin spend for given coin ID."""

        params = {"name": coin_id}
        return await self._mojo_request(POST, "get_uncurried_coin_spend", params)

    
    async def get_transactions_for_coin(self, coin_id):
        """Transactions in which the specified coin was created and spent.

        Arguments:
        coin_id -- coin name (coin ID) as a byte-32 hex encoded string

        Returns the transaction IDs (spend bundle names) as 32-byte hex encoded stings of the spend bundles that created ('added_by') and spent ('removed_by') the coin.
        Since spend bundles are mempool objects, Mojonode may occasionally fail to record a spend, resulting in missing 'added_by' or 'removed_by' data.
        """

        params = {"name": coin_id}
        return await self._mojo_request(POST, "get_transactions_for_coin", params)

    
    async def get_query_schema(self):
        """Mojonode SQL database schema."""
        
        return await self._mojo_request_no_network(POST, "get_query_schema", {})

    
    async def query(self, query):
        """Queries Mojonode SQL database for Chia blockchain data.

        Arguments:
        query -- a valid SQL query as a string
        """

        params = {"query": query}
        return await self._mojo_request_no_network(POST, "query", params)

    
    async def get_latest_singleton_spend(self, address):
        """Latest singleton spend for given address"""

        params = {"address": address}
        return await self._mojo_request(POST, "get_latest_singleton_spend", params)

    
    async def get_routes(self):
        """Available endpoints"""

        if self.base_url == LOCALHOST:
            response = await self._request(POST, "get_routes", {})
            endpoints = response.json()["routes"] + self.mojonode_nonrpc_endpoints
        elif self.base_url == MOJONODE:
            endpoints = MOJONODE_RPC_ENDPOINTS + self.mojonode_nonrpc_endpoints

        # Return available endpoints as HTTP response
        response_data = {
            "routes": endpoints,
            "success": True
        }
        headers = {"Content-Type": "application/json"}
        return httpx.Response(200, content=json.dumps(response_data).encode("utf-8"), headers=headers)

    
    async def close_stream(self, stream_id):
        """Closes an event stream."""
        
        if stream_id in self._streams.keys():
            self._streams.pop(stream_id)
        else:
            raise ValueError(f"No stream with ID {stream_id} to close")
    
    
    async def events(self, for_object=None, from_ts="$", filters=""):
        """Stream events.

        Mojonode disconnects event streams every 5 mins, so that the client needs to reconnect.
        
        Keyword arguments:
        for_object -- only stream events for specified object (coin, block, transaction). Streams all events if set to None
        from_ts -- only stream events from the given timestamp onwards. Note that timestamps are unique
        filters -- only stream events that pass the filter. See Mojonode documentation for details
        """

        if for_object is not None:
            if not for_object in MOJONODE_EVENT_OBJECTS: raise ValueError(f"Unkown object specified ({object})")

        params =  f"&from_ts={from_ts}" + f"&filters={filters}"
        if for_object is not None: endpoint = f"for_object={for_object}&" + params

        stream_id = str(uuid.uuid4())
        self._streams[stream_id] = True
        yield stream_id

        while stream_id in self._streams.keys():
            try:

                # Context manager for Mojonode event stream
                async with self.mojoclient.stream(GET, MOJONODE + "events?" + params, timeout=None) as response:

                    logging.debug(f"Connected to stream ID {stream_id}")

                    try:
                            async for data in response.aiter_lines():

                                if stream_id in self._streams.keys():
                                
                                    if data.startswith('data: '):
                                        event = json.loads(data[6:])
                                        yield event
                                        from_ts = event["ts"]
                                else:
                                    # If stream no longer active, close it
                                    await response.aclose()
                                    logging.debug(f"Closed stream ID {stream_id}")
                                    break
                    except Exception as e:
                        logging.warning(f"Failed to read data from stream ID {stream_id}")
                        
            except Exception as e:
                logging.warning(f"Failed to connect to stream ID {stream_id}")

