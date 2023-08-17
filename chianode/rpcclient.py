import httpx
import json
from .constants import *


class RpcClient():

    def __init__(self, base_url=LOCALHOST, network=MAINNET, debug=False, timeout=5): # 5 second timeout is httpx default
        self.base_url = base_url
        self.network = network
        
        if self.base_url == LOCALHOST:
            self.headers = {"Content-Type": "application/json"}
            self.cert = (f"{CHIA_DIRECTORY}/{self.network}/config/ssl/full_node/private_full_node.crt", f"{CHIA_DIRECTORY}/{self.network}/config/ssl/full_node/private_full_node.key")
        elif self.base_url == MOJONODE:
            self.headers = {"accept": "application/json", "Content-Type": "application/json"}
            self.cert = None
        else:
            raise ValueError(f"Unknown node provider. Base URL: {base_url}")
        
        self.debug = debug
        self.timeout = timeout

        self.client = httpx.AsyncClient(base_url=self.base_url, http2=True, timeout=self.timeout, cert=self.cert, verify=False)


    def _check_heights(self, height_start, height_end):
        
        if not (height_start is None and height_end is None):

            if not (height_start >= 0 and height_end >= 0):
                raise ValueError("Block heights must be non-negative")
            elif height_start >= height_end:
                raise ValueError("Start block height must be less than end block height")
            elif self.base_url == MOJONODE and height_end - height_start > MOJONODE_MAX_HEIGHT_DIFF:
                raise ValueError(f"Block height difference must not be greater than {MOJONODE_MAX_HEIGHT_DIFF} when querying Mojonode")

            
    def _add_network_param(self, params, no_network):
        if not no_network: params["network"] = self.network
        return params

    
    async def _request(self, method, endpoint, params, no_network=False):

        url = self.base_url + endpoint
        data = json.dumps(self._add_network_param(params, no_network))

        if method == POST:

            if self.debug:
                print("Sending POST request")
                print(f"  URL: {url}")
                print(f"  data: {data}")
            response = await self.client.post(url, content=data, headers=self.headers)

        return response

    async def _request_no_network(self, method, endpoint, params):

        return await self._request(method, endpoint, params, no_network=True)
    

    ### Endpoints ###
    #
    # In all of the requests below:
    #   height_start and height_end must be non-negative integers with:
    #     1 <= height_end - height_start <= constants.MOJONODE_MAX_HEIGHT_DIFF
    #   puzzle_hash is a bytes32 hex encoded string
    #   page is the page number to be returned. Mojonode paginates with constants.MOJONODE_PAGE_SIZE items per page

    async def get_coin_record_by_name(self, coin_id):

        params = {"name": coin_id}
        return await self._request(POST, "get_coin_record_by_name", params)

    
    async def get_coin_records_by_names(self, coin_ids, height_start=None, height_end=None, include_spent_coins=False, page=1):

        self._check_heights(height_start, height_end)
        
        # coin_ids must be a list of bytes32 hex encoded strings (eg ["0xdeadbeef", "0xcafef00d"])
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "names": coin_ids
        }
        if self.base_url == MOJONODE:
            params["page"] = page
        elif self.base_url == LOCALHOST:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")
            
        return await self._request(POST, "get_coin_records_by_names", params)

    
    async def get_coin_records_by_parent_ids(self, parent_ids, height_start=None, height_end=None, include_spent_coins=False, page=1):

        self._check_heights(height_start, height_end)

        # Parent_ids is a list of coin parent IDs
        # This call returns all coins who were created (confirmed_block_index) between blocks height_start and height_end (incl)
        # and have one of the parent_ids as their parent coin ID
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "parent_ids": parent_ids
        }
        if self.base_url == MOJONODE:
            params["page"] = page
        elif self.base_url == LOCALHOST:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")
            
        return await self._request(POST, "get_coin_records_by_parent_ids", params)

    
    async def get_coin_records_by_puzzle_hash(self, puzzle_hash, height_start=None, height_end=None, include_spent_coins=False, page=1):

        self._check_heights(height_start, height_end)
        
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "puzzle_hash": puzzle_hash
        }
        if self.base_url == MOJONODE:
            params["page"] = page
        elif self.base_url == LOCALHOST:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        return await self._request(POST, "get_coin_records_by_puzzle_hash", params)

    
    async def get_coin_records_by_puzzle_hashes(self, puzzle_hashes, height_start=None, height_end=None, include_spent_coins=False, page=1):

        self._check_heights(height_start, height_end)
        
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "puzzle_hashes": puzzle_hashes
        }
        if self.base_url == MOJONODE:
            params["page"] = page
        elif self.base_url == LOCALHOST:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        return await self._request(POST, "get_coin_records_by_puzzle_hashes", params)

    
    async def get_coin_records_by_hint(self, hint, height_start=None, height_end=None, include_spent_coins=False, page=1):

        self._check_heights(height_start, height_end)
        
        # hint is a bytes32 hex encoded string
        # For info on hints see: https://docs.chia.net/conditions/?_highlight=hint#hinting

        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "hint": hint
        }
        if self.base_url == MOJONODE:
            params["page"] = page
        elif self.base_url == LOCALHOST:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        return await self._request(POST, "get_coin_records_by_hint", params)

    
    async def get_block_record_by_height(self, height):

        params = {"height": height}
        return await self._request(POST, "get_block_record_by_height", params)

    
    async def get_block_record(self, header_hash):

        params = {"header_hash": header_hash}
        return await self._request(POST, "get_block_record", params)

    
    async def get_block_records(self, height_start=0, height_end=100):

        # This call requires a block height range to be provided
        if height_start is None or height_end is None:
            raise ValueError("Starting and ending block heights must be provided (cannot be None)")
        
        self._check_heights(height_start, height_end)
    
        params = {"start": height_start, "end": height_end}
        return await self._request(POST, "get_block_records", params)

    
    async def get_block(self, header_hash):

        params = {"header_hash": header_hash}
        return await self._request(POST, "get_block", params)

    
    async def get_blocks(self, height_start, height_end):

        # This call requires a block height range to be provided
        if height_start is None or height_end is None:
            raise ValueError("Starting and ending block heights must be provided (cannot be None)")

        self._check_heights(height_start, height_end)

        params = {"start": height_start, "end": height_end}
        return await self._request(POST, "get_blocks", params)

        
    async def get_additions_and_removals(self, header_hash):

        params = {"header_hash": header_hash}
        return await self._request(POST, "get_additions_and_removals", params)

    
    async def get_block_count_metrics(self):

        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_block_count_metrics", {})
        else:
            raise ValueError(f"Endpoint get_block_count_metrics not supported by node provider ({self.base_url})")

        
    async def get_blockchain_state(self):

        return await self._request(POST, "get_blockchain_state", {})

    
    async def get_puzzle_and_solution(self, coin_id, height=None):

        # coin_id is a bytes32 hex encoded string
        # height is the height at which the coin was spent
        # Mojonode doesn't require the height parameter, only coin_id

        params = {"coin_id": coin_id}
        
        # Check that height is provided if we are not using Mojonode
        if not self.base_url == "https://api.mojonode.com/":
            if not height >= 0:
                raise ValueError("Must provide height at which coin was spent")
            else:
                params["height"] = height
            
        return await self._request(POST, "get_puzzle_and_solution", params)

    
    async def get_block_spends(self, header_hash):

        params = {"header_hash": header_hash}
        return await self._request(POST, "get_block_spends", params)

    
    async def get_all_mempool_items(self):

        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_all_mempool_items", {})
        else:
            raise ValueError(f"Endpoint get_all_mempool_items not supported by node provider ({self.base_url})")

        
    async def get_all_mempool_tx_ids(self):

        return await self._request(POST, "get_all_mempool_tx_ids", {})

    
    async def get_mempool_item_by_tx_id(self, tx_id):

        # tx_id is a bytes32 hex encoded string
        
        params = {"tx_id": tx_id}
        return await self._request(POST, "get_mempool_item_by_tx_id", params)

    
    async def get_initial_freeze_period(self):

        return await self._request(POST, "get_initial_freeze_period", {})

    
    async def healthz(self):

        return await self._request(POST, "healthz", {})

    
    async def get_fee_estimate(self, spend_bundle=None, cost=None, target_times=None):

        # Either spend_bundle or cost must be provided (but not both).
        # For details on transaction costs in Chia see https://chialisp.com/costs
        # target_times is a list of target times (>= 0 in seconds counting from now) for transaction inclusion.
        # The response contains an 'estimate' field, which returns a list of fee
        # estimates corresponding to the list of target times.

        # Check that target times are well-defined
        if target_times is None:
            target_times = [0]
        elif isinstance(target_times, list):
            for tt in target_times:
                if not tt >=0: raise ValueError("Target times must be greater than or equal to 0")
        else:
            TypeError("Parameter 'target_times' must be a list")

        params = {
            "target_times": target_times
        }

        # Check that either spend_bundle or cost is provided
        if spend_bundle is None and cost is None:
            ValueError("Must provide a value for either 'spend_bundle' or 'cost' parameter")
        elif spend_bundle is not None and cost is not None:
            ValueError("Either 'spend_bundle' or 'cost' parameter must be None")
        elif spend_bundle is not None:
            if not isinstance(spend_bundle, dict):
                TypeError("Parameter 'spend_bundle' must be a dict")
            else:
                params["spend_bundle"] = spend_bundle
        else:
            params["cost"] = cost

        # Send request
        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_fee_estimate", params)
        else:
            raise ValueError(f"Endpoint get_fee_estimate not supported by node provider ({self.base_url})")

        
    async def push_tx(self, spend_bundle):

        params = {"spend_bundle": spend_bundle}
        return await self._request(POST, "push_tx", params)

    
    async def get_network_info(self):

        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_network_info", {})
        else:
            raise ValueError(f"Endpoint get_network_info not supported by node provider ({self.base_url})")

        
    async def get_network_space(self, block_header_hash_start, block_header_hash_end):

        params = {
            "older_block_header_hash": block_header_hash_start,
            "newer_block_header_hash": block_header_hash_end
        }
        
        # The network space value returned is given in bytes.
        # To get the network space in EiB, the returned value needs to be divided by 2^60
        
        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_network_space", params)
        else:
            raise ValueError(f"Endpoint get_network_space not supported by node provider ({self.base_url})")


    async def get_recent_signage_point_or_eos(self, signage_point_hash=None, challenge_hash=None):

        # Either signage point hash or challenge hash need to be provided (but not both)
        # Whichever parameters is provided must be a bytes32 hex encoded string

        # Check that either spend_bundle or cost is provided
        if signage_point_hash is None and challenge_hash is None:
            ValueError("Must provide a value for either 'signage_point_hash' or 'challenge_hash' parameter")
        elif spend_bundle is not None and cost is not None:
            ValueError("Either 'signage_point_hash' or 'challenge_hash' parameter must be None")
        elif signage_point_hash is not None:
            params["sp_hash"] = signage_point_hash
        else:
            params["challenge_hash"] = challenge_hash
        
        # The network space value returned is given in bytes.
        # To get the network space in EiB, the returned value needs to be divided by 2^60
        
        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_signage_point_or_eos", params)
        else:
            raise ValueError(f"Endpoint get_signage_point_or_eos not supported by node provider ({self.base_url})")

        
    async def get_unfinished_block_headers(self):

        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_unfinished_block_headers", {})
        else:
            raise ValueError(f"Endpoint get_unfinished_block_headers not supported by node provider ({self.base_url})")

        
    async def get_routes(self):

        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_routes", {})
        elif self.base_url == MOJONODE:
            response_data = {
                "routes": MOJONODE_RPC_ENDPOINTS,
                "success": True
            }
            headers = {"Content-Type": "application/json"}
            return httpx.Response(200, content=json.dumps(response_data).encode("utf-8"), headers=headers)
