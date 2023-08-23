import os
import httpx
import yaml
import json
import logging
from datetime import datetime
from .constants import NEWLINE, LOCALHOST, MOJONODE, MAINNET, POST, MOJONODE_MAX_HEIGHT_DIFF, MOJONODE_RPC_ENDPOINTS


logging.getLogger(__name__).addHandler(logging.NullHandler())


class RpcClient():
    """Client class to query Chia nodes via RPCs.

    For a documentation of the official Chia RPCs see: https://docs.chia.net/full-node-rpc/
    For a documentation of Mojonode RPCs see: https://api.mojonode.com/docs
    
    There are conventions for certain public method arguments of this class:
      * height_start and height_end must be non-negative integers that satify
         1 <= height_end - height_start <= constants.MOJONODE_MAX_HEIGHT_DIFF
      * The block at height_start is included, the block at height_end is excluded
      * puzzle_hash, coin_id, hint, and header_hash are 32-byte hex encoded strings
      * puzzle_hashes, coin_ids, and parent_ids are lists of 32-byte hex encoded strings
      * include_spent_coins is a boolean value indicating whether to include spent coins
      * When querying Mojonode, page is the number of the page to be returned, starting from 1.
        Mojonode paginates data with constants.MOJONODE_PAGE_SIZE items per page.
        The page paramenter is ignored when querying nodes that don't support pagination.
    
    Note that results returned by Mojonode are not sorted.
    """

    def __init__(self, base_url=LOCALHOST, network=MAINNET, timeout=5): # 5 second timeout is httpx default
        """Initialize an RpcClient instance.
        
        Keywork arguments:
        base_url -- the URL (exluding endpoint) to query
        network -- the network to query
        timeout -- timeout in seconds for requests to the node
        """

        self.base_url = base_url

        if self.base_url == LOCALHOST:
            if os.getenv('CHIA_ROOT') is None: raise NameError("Environment variable CHIA_ROOT not set")
            with open(os.getenv('CHIA_ROOT') + "/config/config.yaml", "r") as file:
                config_file = yaml.safe_load(file)
                selected_network = config_file["full_node"]["selected_network"]
            if selected_network == network:
                self.network = network
            else:
                raise ValueError(f"Please connect the node running on localhost to {network}")
            self.headers = {"Content-Type": "application/json"}
            chia_root = "/".join(os.getenv('CHIA_ROOT').split("/")[:-1])
            self.cert = (f"{chia_root}/{self.network}/config/ssl/full_node/private_full_node.crt", f"{chia_root}/{self.network}/config/ssl/full_node/private_full_node.key")
        elif self.base_url == MOJONODE:
            self.network= network
            self.headers = {"accept": "application/json", "Content-Type": "application/json"}
            self.cert = None
        else:
            raise ValueError(f"Unknown node provider. Base URL: {base_url}")

        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, http2=True, timeout=self.timeout, cert=self.cert, verify=False)


    def _check_heights(self, height_start, height_end):
        """Check that start and end block heights are valid and consistent.

        Arguments:
        height_start -- starting block height (incl)
        height_end -- ending blok height (excl)
        """
        
        if not (height_start is None and height_end is None):

            if not (height_start >= 0 and height_end >= 0):
                raise ValueError("Block heights must be non-negative")
            elif height_start >= height_end:
                raise ValueError("Start block height must be less than end block height")
            elif self.base_url == MOJONODE and height_end - height_start > MOJONODE_MAX_HEIGHT_DIFF:
                raise ValueError(f"Block height difference must not be greater than {MOJONODE_MAX_HEIGHT_DIFF} when querying Mojonode")

            
    def _add_network_param(self, params, no_network):
        """Add a network field to a dict of parameters.

        Arguments:
        params -- dict of parameters
        no_network -- boolean indicating whether to add a network field to params
        """
        
        if not no_network: params["network"] = self.network
        return params

    
    async def _request(self, method, endpoint, params, no_network=False):
        """Send a REST request.

        Arguments:
        method -- a REST method (GET, POST, etc)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters

        Keywork arguments:
        no_network -- boolean indicating whether to add a network field to params
        """

        url = self.base_url + endpoint
        data = json.dumps(self._add_network_param(params, no_network))

        if method == POST:
            logging.info(f"Sending POST request{NEWLINE}  URL: {url}{NEWLINE}  data: {data}")
            response = await self.client.post(url, content=data, headers=self.headers)
        else:
            raise ValueError(f"Unsupported REST method {method}")

        return response

    async def _request_no_network(self, method, endpoint, params):
        """Send a REST request without specifying a network.

        Arguments:
        method -- a REST method (GET, POST, etc.)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters
        """

        return await self._request(method, endpoint, params, no_network=True)

    
    async def get_coin_record_by_name(self, coin_id):

        params = {"name": coin_id}
        return await self._request(POST, "get_coin_record_by_name", params)

    
    async def get_coin_records_by_names(self, coin_ids, height_start=None, height_end=None, include_spent_coins=False, page=1):
        
        self._check_heights(height_start, height_end)
        
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
        """Return coin records for coins hinted at.

        For info on hints see https://docs.chia.net/conditions/?_highlight=hint#hinting
        
        Arguments:
        hint -- a hint as a 32-byte hex encoded string

        Keyword arguments:
        height_start -- starting block height (incl)
        height_end -- ending block height (excl)
        include_spent_coins -- boolean indicating whether to include spent coins
        page -- page to be returned (if applicable)
        """

        self._check_heights(height_start, height_end)

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
        """Returns a fee estimate

        Either spend_bundle or cost must be provided (but not both).
        For details on transaction costs in Chia see https://chialisp.com/costs

        Keyword arguments:
        spend_bundle -- spend bundle as a dict
        cost -- cost of transaction
        target_times -- list of target times for transaction inclusion in seconds counting from now

        The response contains an 'estimate' field, which is a list of fee estimates corresponding to the list of target times specified.
        """

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
        """Returns the average Chia network space between two blocks.

        Arguments:
        block_header_hash_start -- block header hash of starting block
        block_header_hash_end -- block header hash of ending block
        
        The network space value returned is given in bytes. To get the network space in EiB, the returned value needs to be divided by 2^60
        """

        params = {
            "older_block_header_hash": block_header_hash_start,
            "newer_block_header_hash": block_header_hash_end
        }
        
        if self.base_url == LOCALHOST:
            return await self._request(POST, "get_network_space", params)
        else:
            raise ValueError(f"Endpoint get_network_space not supported by node provider ({self.base_url})")


    async def get_recent_signage_point_or_eos(self, signage_point_hash=None, challenge_hash=None):
        """Return the most recent signage point for a given signage point hash or challenge hash.
        
        Either signage_point_hash or challenge_hash needs to be provided (but not both)

        signage_point_hash -- signage point hash as a 32-byte hex encoded string
        challenge_hash -- challenge hash as a 32-byte hex encoded string
        """

        # Check that either spend_bundle or cost is provided
        if signage_point_hash is None and challenge_hash is None:
            ValueError("Must provide a value for either 'signage_point_hash' or 'challenge_hash' parameter")
        elif spend_bundle is not None and cost is not None:
            ValueError("Either 'signage_point_hash' or 'challenge_hash' parameter must be None")
        elif signage_point_hash is not None:
            params["sp_hash"] = signage_point_hash
        else:
            params["challenge_hash"] = challenge_hash
        
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
