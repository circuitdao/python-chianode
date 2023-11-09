import logging
import httpx
import uuid
import json
from typing import Any, Dict, List, Optional, Tuple, cast

from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_record import CoinRecord
from chia.types.coin_spend import CoinSpend

from .constants import NEWLINE, GET, POST, NodeProvider, Network, MOJONODE_STANDARD_ENDPOINTS, MOJONODE_NONSTANDARD_ENDPOINTS
from .standardclient import StandardClient
from .utils import hexstr_to_bytes32, coin_record_dict_backwards_compat, convert_tx, convert_uncurried_coin_spend, convert_coin_transactions


from pprint import pprint


logging.getLogger(__name__).addHandler(logging.NullHandler())

    
class MojoClient(StandardClient):
    """Client to make RPCs to Mojonode.

    This client supports the remote procecure call (RPC) interface exposed by Mojonode.

    Mojonode does not support all standard RPCs. To have access to all standard RPCs and Mojonode endpoints,
    the StandardClient base class of a MojoClient instance can be connected to an official Chia full node running on localhost.
    Using an official Chia full node running on localhost for standard RPCs can also be desirable for performance reasons.

    For the Mojonode RPC interface documentation, see https://api.mojonode.com/docs.

    Conventions for public method arguments and return values:
      * The block at height_start is included, the block at height_end is excluded
      * By default, spent coins are not included in the result to match the behaviour of the offical Chia full node RPC rather than Mojonode
      * When querying Mojonode:
         - height_start and height_end must be non-negative integers that satify
             1 <= height_end - height_start <= constants.MOJONODE_MAX_HEIGHT_DIFF (currently 100)
         - data returned is not sorted
         - data returned is paginated
         - the page parameter can be used to specify which page to return, starting from 1
         - by default, the page 1 is returned
         - the number of items per page is specified by constants.MOJONODE_PAGE_SIZE (currently 50)
      *  The page parameter is ignored when querying nodes that don't support pagination.
    """

    def __init__(
            self,
            network: Network = Network.MAINNET,
            timeout: Optional[int] = 10,
            standard_node_provider: NodeProvider = NodeProvider.MOJONODE,
            standard_node_timeout: Optional[int] = 5 # 5 second timeout is the httpx default
    ): 
        """Initialize a MojoClient instance.

        Keywork arguments:
        network -- network which the node provider is connected to. Default is Network.MAINNET
        timeout -- timeout in seconds for requests to Mojonode. Set to None for no timeout. Default is 10 seconds
        standard_node_provider -- node provider for standard remote procecure calls (RPCs). Default is NodeProvider.MOJONODE
        standard_node_timeout -- timeout in seconds for standard RPCs. Default is 5 seconds. Set to None for no timeout. Gets overwritten by the timeout argument if Mojonode is the standard node provider.
        """

        if timeout is not None and timeout < 0: ValueError("Timeout must be None or a non-negative integer")
        if standard_node_provider == NodeProvider.MOJONODE: standard_node_timeout = timeout # Override standard node timeout if Mojonode used as standard node provider
        StandardClient.__init__(self, node_provider=standard_node_provider, network=Network.MAINNET, timeout=standard_node_timeout)
        
        self.mojo_headers = {"accept": "application/json", "Content-Type": "application/json"}
        self.mojo_timeout = timeout

        self._streams = {}
        
        if standard_node_provider == NodeProvider.MOJONODE:
            self.mojoclient = self.client
        else:
            self.mojoclient = httpx.AsyncClient(base_url=NodeProvider.MOJONODE.base_url(), http2=True, timeout=self.mojo_timeout)

            
    async def _mojo_request(self, method: str, endpoint: str, params: dict, no_network: bool =False, timeout: Optional[int] =-1):
        """Send a REST request to Mojonode.

        Arguments:
        method -- a REST method (GET, POST, etc)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters

        Keyword arguments:
        no_network -- boolean indicating whether to add a network field to params
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        url = NodeProvider.MOJONODE.base_url() + "/" + endpoint
        data = json.dumps(self._add_network_param(params, no_network))

        if method == POST:
            logging.info(f"Sending POST request{NEWLINE}  URL: {url}{NEWLINE}  data: {data}")
            response = await self.mojoclient.post(url, content=data, headers=self.mojo_headers)
        else:
            raise ValueError(f"Unsupported REST method {method}")

        return response

    
    async def _mojo_request_no_network(self, method: str, endpoint: str, params: dict, timeout: Optional[int] =-1):
        """Send a REST request to Mojonode without specifying a network

        Arguments:
        method -- a REST method (GET, POST, etc)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        return await self._mojo_request(method, endpoint, params, no_network=True)


    async def get_tx_by_name(self, tx_id: bytes32, timeout: Optional[int] =-1) -> Dict[str, Any]:
        """Transaction by transaction ID.

        Arguments:
        tx_id -- a spend bundle name

        Keyword arguments:
        timeout -- request timeout in seconds

        Returns the transaction (spend bundle) corresponding to the transaction ID (spend bundle name).
        Since spend bundles are mempool objects, Mojonode may occasionally fail to record a spend, resulting in missing data.
        """

        params = {"name": tx_id.hex()}

        transaction = (await self._mojo_request(POST, "get_tx_by_name", params)).json()["transaction"]

        return convert_tx(transaction)

    
    async def get_uncurried_coin_spend(self, coin_id: bytes32, timeout: Optional[int] =-1) -> Dict[str, Any]:
        """Uncurried coin spend for given coin ID.
        
        Arguments:
        coin_id -- a coin ID (coin name)
        
        Keyword arguments:
        timeout -- request timeout in seconds

        Returns a dict with modified keys in the 'puzzle' sub-dict returned by Mojonode.
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        params = {"name": coin_id.hex()}

        uncurried_coin_spend = (await self._mojo_request(POST, "get_uncurried_coin_spend", params)).json()["uncurried_coin_spend"]

        return convert_uncurried_coin_spend(uncurried_coin_spend)

    
    async def get_transactions_for_coin(self, coin_id: bytes32, timeout: Optional[int] =-1) -> Dict[str, bytes32]:
        """Transactions in which the specified coin was created and spent.

        Arguments:
        coin_id -- a coin ID (coin name)

        Keyword arguments:
        timeout -- request timeout in seconds        

        Returns transaction IDs (spend bundle names) of the spend bundles that created ('added_by') and spent ('removed_by') the coin, respectively.
        Since transactions are mempool objects, Mojonode may occasionally fail to record a transaction, resulting in missing 'added_by' or 'removed_by' data.
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        params = {"name": coin_id.hex()}

        coin_transactions = (await self._mojo_request(POST, "get_transactions_for_coin", params)).json()["coin_transactions"]
        
        return convert_coin_transactions(coin_transactions)

    
    async def get_query_schema(self, timeout: Optional[int] =-1) -> List[Dict[str, Any]]:
        """Mojonode SQL database schema.

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        query_schema = (await self._mojo_request_no_network(POST, "get_query_schema", {})).json()
        
        return cast(List[Dict[str, Any]], query_schema)

    
    async def query(self, query, timeout: Optional[int] =-1) -> dict:
        """Queries Mojonode SQL database for Chia blockchain data.

        Depending on the complexity of the query, this call make take a long time to return a response.
        It may be necessary to use a timeout greater than the default, or even setting timeout = None.

        Arguments:
        query -- a valid SQL query as a string

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        params = {"query": query}

        response = (await self._mojo_request_no_network(POST, "query", params)).json()
        
        return response

    
    async def get_latest_singleton_spend(self, address: str, timeout: Optional[int] =-1) -> Tuple[CoinSpend, CoinRecord]:
        """Latest singleton spend and current coin for given address (launcher ID)

        Arguments:
        address -- address of a singleton

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        params = {"address": address}

        response = (await self._mojo_request(POST, "get_latest_singleton_spend", params)).json()
        
        return (
            CoinSpend.from_json_dict(response["latest_spend"]),
            CoinRecord.from_json_dict(coin_record_dict_backwards_compat(response["current_coin"]))
        )
         
    
    async def get_routes(self, timeout: Optional[int] =-1) -> List[str]:
        """Available endpoints

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.mojo_timeout

        if self.node_provider == NodeProvider.FULLNODE:
            routes = (await self._request(POST, "get_routes", {})).json()["routes"]
            endpoints = routes + MOJONODE_NONSTANDARD_ENDPOINTS
        elif self.node_provider == NodeProvider.MOJONODE:
            endpoints = MOJONODE_STANDARD_ENDPOINTS + MOJONODE_NONSTANDARD_ENDPOINTS

        return endpoints

    
    async def close_stream(self, stream_id: str):
        """Closes an event stream.

        Arguments:
        stream_id -- ID of the event stream to close
        """

        if stream_id in self._streams.keys():
            self._streams.pop(stream_id)
        else:
            raise ValueError(f"No stream with ID {stream_id} to close")

        
    async def events(self, for_object: str =None, from_ts: str ="$", filters=""):
        """Stream events.

        Mojonode disconnects event streams every 5 mins. This function client automatically reconnects.
        
        Keyword arguments:
        for_object -- only stream events for specified object (coin, block, transaction). Streams all events if set to None
        from_ts -- only stream events from the given timestamp (Unix epoch in seconds) onwards ("$" to start from now). Timestamps are unique
        filters -- only stream events that pass the filter. See Mojonode documentation for details: https://api.mojonode.com/docs#/mojonode/mojonode_chiadata_views_subscribe
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
                async with self.mojoclient.stream(GET, NodeProvider.MOJONODE.base_url() + "/events?" + params, timeout=None) as response:

                    logging.debug(f"Connected to stream. Assigned stream ID {stream_id}")

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

