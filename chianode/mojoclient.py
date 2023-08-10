import httpx
import uuid
import json
from datetime import datetime
from .rpcclient import RpcClient, MOJONODE_RPC_ENDPOINTS
from .constants import GET, POST, MAINNET, LOCALHOST, MOJONODE

    
class MojoClient(RpcClient):

    def __init__(self, base_url=MOJONODE, network=MAINNET, debug=False, mojo_timeout=10, rpc_timeout=5): # 5 second timeout is the httpx default
        if base_url == MOJONODE: rpc_timeout = mojo_timeout # Override RPC timeout if Mojonode used for RPC calls
        RpcClient.__init__(self, base_url=base_url, network=MAINNET, debug=debug, timeout=rpc_timeout)
        
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

        url = MOJONODE + endpoint
        data = json.dumps(self._add_network_param(params, no_network))

        if method == POST:

            if self.debug:
                print("Sending POST request")
                print(f"  URL: {url}")
                print(f"  data: {data}")
            response = await self.mojoclient.post(url, content=data, headers=self.mojo_headers)

        return response
    
    async def _mojo_request_no_network(self, method, endpoint, params):

        return await self._mojo_request(method, endpoint, params, no_network=True)


    ### Endpoints ###
    async def get_tx_by_name(self, coin_id):

        params = {"name": coin_id}
        return await self._mojo_request(POST, "get_tx_by_name", params)

    
    async def get_uncurried_coin_spend(self, coin_id):

        params = {"name": coin_id}
        return await self._mojo_request(POST, "get_uncurried_coin_spend", params)

    
    async def get_transactions_for_coin(self, coin_id):

        params = {"name": coin_id}
        return await self._mojo_request(POST, "get_transactions_for_coin", params)

    
    # Return Mojonode SQL database schema
    async def get_query_schema(self):

        return await self._mojo_request_no_network(POST, "get_query_schema", {})

    
    # Query Mojonode SQL database for Chia blockchain data
    async def query(self, query):

        params = {"query": query}
        return await self._mojo_request_no_network(POST, "query", params)

    
    async def get_latest_singleton_spend(self, address):

        params = {"address": address}
        return await self._mojo_request(POST, "get_latest_singleton_spend", params)

    
    async def get_routes(self):

        if self.base_url == LOCALHOST:
            response = await self._request(POST, "get_routes", {})
            endpoints = response.json()["routes"] + self.mojonode_nonrpc_endpoints
        elif self.base_url == MOJONODE:
            endpoints = MOJONODE_RPC_ENDPOINTS + self.mojonode_nonrpc_endpoints

        # Return endpoints as HTTP response
        response_data = {
            "routes": endpoints,
            "success": True
        }
        headers = {"Content-Type": "application/json"}
        return httpx.Response(200, content=json.dumps(response_data).encode("utf-8"), headers=headers)

    
    async def close_stream(self, stream_id):
        if stream_id in self._streams.keys():
            self._streams.pop(stream_id)
        else:
            raise ValueError(f"No stream with ID {stream_id} to close")
    
    
    # Endpoint for streaming events
    async def events(self, for_object=None, from_ts="$", filters=""):

        if for_object is not None:
            if not for_object in MOJONODE_EVENT_OBJECTS: raise ValueError(f"Unkown object specified ({object})")

        params =  f"&from_ts={from_ts}" + f"&filters={filters}"
        if for_object is not None: endpoint = f"for_object={for_object}&" + params

        stream_id = str(uuid.uuid4())
        self._streams[stream_id] = True
        yield stream_id

        # Mojonode server automatically disconnects every 5 mins
        while stream_id in self._streams.keys():
            try:

                # Context manager for Mojonode event stream
                async with self.mojoclient.stream(GET, MOJONODE + "events?" + params, timeout=None) as response:

                    if self.debug: print(f"CONNECTED TO STREAM ID {stream_id} at {datetime.utcnow()} UTC")

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
                                    if self.debug: print(f"CLOSED STREAM ID {stream_id} at {datetime.utcnow()} UTC")
                                    break
                    except Exception as e:
                        print(e)
                        
            except Exception as e:
                print(e)

