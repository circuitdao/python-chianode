import os
import httpx
import yaml
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, cast

from chia.consensus.block_record import BlockRecord
from chia.full_node.signage_point import SignagePoint
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.blockchain_format.coin import Coin
from chia.types.coin_record import CoinRecord
from chia.types.coin_spend import CoinSpend
from chia.types.end_of_slot_bundle import EndOfSubSlotBundle
from chia.types.full_block import FullBlock
from chia.types.mempool_item import MempoolItem
from chia.types.spend_bundle import SpendBundle
from chia.types.unfinished_header_block import UnfinishedHeaderBlock
from chia.util.byte_types import hexstr_to_bytes

from .constants import NEWLINE, NodeProvider, Network, POST, MOJONODE_MAX_HEIGHT_DIFF, MOJONODE_STANDARD_ENDPOINTS, UNSUPPORTED_STANDARD_ENDPOINTS
from .utils import hexstr_to_bytes32, coin_record_dict_backwards_compat, convert_mempool_item


logging.getLogger(__name__).addHandler(logging.NullHandler())


class StandardClient():
    """Client to make standard RPCs to a Chia node.

    This client supports the remote procecure calls (RPCs) of the official Chia full node.
    There are some minor variations - both in terms of arguments and return values  - vs the official interace.

    The client can connect to either an official Chia full node running on localhost or Mojonode as node provider.

    Official Chia full node RPC interface documentation:
    * https://docs.chia.net/full-node-rpc (includes modifications for command line use)
    * https://github.com/Chia-Network/chia-blockchain/blob/main/chia/rpc/full_node_rpc_client.py

    Mojonode RPC interface documentation:
    * https://api.mojonode.com/docs
    
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
            node_provider: NodeProvider = NodeProvider.OFFICIALNODE,
            network: Network = Network.MAINNET,
            timeout: Optional[int] = 5 # 5 second timeout is httpx default
    ): 
        """Initialize a StandardClient instance.

        Keywork arguments:
        node_provider -- node provider for standard RPCs. Default is NodeProvider.OFFICIALNODE
        network -- network which the node provider is connected to. Default is Network.MAINNET
        timeout -- timeout in seconds for requests to the node provider. Default is 10 seconds. Set to None for no timeout
        """

        self.node_provider = node_provider

        if self.node_provider == NodeProvider.OFFICIALNODE:
            if os.getenv('CHIA_ROOT') is None: raise NameError("Environment variable CHIA_ROOT not set")
            chia_root = os.getenv("CHIA_ROOT")
            with open(chia_root + "/config/config.yaml", "r") as file:
                config_file = yaml.safe_load(file)
                selected_network = config_file["full_node"]["selected_network"]
                rpc_port = config_file["full_node"]["rpc_port"]
            if selected_network == network.name.lower():
                self.network = network
                self.base_url = f"{self.node_provider.base_url()}:{rpc_port}"
            else:
                raise ValueError(f"Please connect the node running on localhost to {network.name}")
            self.headers = {"Content-Type": "application/json"}
            if self.network in [Network.MAINNET, Network.TESTNET10]:
                config_base_path = f'{"/".join(chia_root.split("/")[:-1])}/{self.network.name.lower()}'
                self.cert = (f"{config_base_path}/config/ssl/full_node/private_full_node.crt", f"{config_base_path}/config/ssl/full_node/private_full_node.key")
            elif self.network == Network.SIMULATOR0:
                self.cert = (f"{chia_root}/config/ssl/full_node/private_full_node.crt", f"{chia_root}/config/ssl/full_node/private_full_node.key")
            else:
                raise ValueError(f"Unknown network {self.network.name}")
        elif self.node_provider == NodeProvider.MOJONODE:
            self.base_url = self.node_provider.base_url()
            if network not in [Network.MAINNET]:
                raise ValueError(f"Mojonode does not support network {network.name}")
            self.network= network
            self.headers = {"accept": "application/json", "Content-Type": "application/json"}
            self.cert = None
        else:
            raise ValueError(f"Unknown node provider {self.node_provider.name}")

        if timeout is not None and timeout < 0: ValueError("Timeout must be None or a non-negative integer")
        
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, http2=True, timeout=self.timeout, cert=self.cert, verify=False)


    def _check_heights(self, height_start: int, height_end: int) -> bool:
        """Returns True if start and end block heights are valid and consistent, and otherwise throws an exception.

        Arguments:
        height_start -- starting block height (incl)
        height_end -- ending blok height (excl)
        """
        
        if not (height_start is None and height_end is None):

            if not (height_start >= 0 and height_end >= 0):
                raise ValueError("Block heights must be non-negative")
            elif height_start >= height_end:
                raise ValueError("Start block height must be less than end block height")
            elif self.node_provider == NodeProvider.MOJONODE and height_end - height_start > MOJONODE_MAX_HEIGHT_DIFF:
                raise ValueError(f"Block height difference must not be greater than {MOJONODE_MAX_HEIGHT_DIFF} when querying Mojonode")

        return True
    
            
    def _add_network_param(self, params: dict, no_network: bool) -> dict:
        """Add a network field to a dict of parameters.

        Arguments:
        params -- dict of parameters
        no_network -- boolean indicating whether to add a network field to params
        """
        
        if not no_network: params["network"] = self.network.name.lower()
        return params

    
    async def _request(self, method: str, endpoint: str, params: dict, no_network: bool =False, timeout: Optional[int] =-1):
        """Send a REST request.

        Arguments:
        method -- a REST method (always POST)
        endpoint -- URI endpoint to send request to
        params -- request parameters

        Keywork arguments:
        no_network -- boolean indicating whether to add a network field to params
        timeout -- request timeout in seconds
        """
        
        if timeout is not None and timeout < 0: timeout = self.timeout        

        url = self.base_url + "/" + endpoint
        data = json.dumps(self._add_network_param(params, no_network))

        if method == POST:
            logging.info(f"Sending POST request{NEWLINE}  URL: {url}{NEWLINE}  data: {data}")
            response = await self.client.post(url, content=data, headers=self.headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported REST method {method}")

        return response

    async def _request_no_network(self, method: str, endpoint: str, params: dict, timeout: Optional[int] =-1):
        """Send a REST request without specifying a network.

        Arguments:
        method -- a REST method (GET, POST, etc.)
        endpoint -- URI endpoint to send request to
        params -- dict of request parameters

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.timeout

        return await self._request(method, endpoint, params, no_network=True, timeout=timeout)

    
    async def get_coin_record_by_name(self, coin_id: bytes32, timeout: Optional[int] =-1) -> CoinRecord:

        if timeout is not None and timeout < 0: timeout = self.timeout

        params = {"name": coin_id.hex()}

        coin_record = (await self._request(POST, "get_coin_record_by_name", params)).json()["coin_record"]

        return CoinRecord.from_json_dict(coin_record_dict_backwards_compat(coin_record))

    
    async def get_coin_records_by_names(
            self,
            coin_ids: List[bytes32],
            height_start: Optional[int] =None,
            height_end: Optional[int] =None,
            include_spent_coins: bool =False,
            page: int =1,
            timeout: Optional[int] =-1
    ) -> List[CoinRecord]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        self._check_heights(height_start, height_end)
        
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "names": [cid.hex() for cid in coin_ids]
        }
        if self.node_provider == NodeProvider.MOJONODE:
            params["page"] = page
        elif self.node_provider == NodeProvider.OFFICIALNODE:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        coin_records = (await self._request(POST, "get_coin_records_by_names", params, timeout=timeout)).json()["coin_records"]

        return [CoinRecord.from_json_dict(coin_record_dict_backwards_compat(cr)) for cr in coin_records]

    
    async def get_coin_records_by_parent_ids(
            self,
            parent_ids: List[bytes32],
            height_start: Optional[int] =None,
            height_end: Optional[int] =None,
            include_spent_coins: bool =False,
            page: int =1,
            timeout: Optional[int] =-1
    ) -> List[CoinRecord]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        self._check_heights(height_start, height_end)

        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "parent_ids": [pid.hex() for pid in parent_ids]
        }
        if self.node_provider == NodeProvider.MOJONODE:
            params["page"] = page
        elif self.node_provider == NodeProvider.OFFICIALNODE:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        coin_records = (await self._request(POST, "get_coin_records_by_parent_ids", params)).json()["coin_records"]

        return [CoinRecord.from_json_dict(coin_record_dict_backwards_compat(cr)) for cr in coin_records]

    
    async def get_coin_records_by_puzzle_hash(
            self,
            puzzle_hash: bytes32,
            height_start: Optional[int] =None,
            height_end: Optional[int] =None,
            include_spent_coins: bool =False,
            page: int =1,
            timeout: Optional[int] =-1
    ) -> List[CoinRecord]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        self._check_heights(height_start, height_end)
        
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "puzzle_hash": puzzle_hash.hex()
        }
        if self.node_provider == NodeProvider.MOJONODE:
            params["page"] = page
        elif self.node_provider == NodeProvider.OFFICIALNODE:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")


        coin_records = (await self._request(POST, "get_coin_records_by_puzzle_hash", params, timeout=timeout)).json()["coin_records"]

        return [CoinRecord.from_json_dict(coin_record_dict_backwards_compat(cr)) for cr in coin_records]

        
    async def get_coin_records_by_puzzle_hashes(
            self,
            puzzle_hashes: List[bytes32],
            height_start: Optional[int] =None,
            height_end: Optional[int] =None,
            include_spent_coins: bool =False,
            page: int =1,
            timeout: Optional[int] =-1
    ) -> List[CoinRecord]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        self._check_heights(height_start, height_end)
        
        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "puzzle_hashes": [ph.hex() for ph in puzzle_hashes]
        }
        if self.node_provider == NodeProvider.MOJONODE:
            params["page"] = page
        elif self.node_provider == NodeProvider.OFFICIALNODE:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        coin_records = (await self._request(POST, "get_coin_records_by_puzzle_hashes", params, timeout=timeout)).json()["coin_records"]

        return [CoinRecord.from_json_dict(coin_record_dict_backwards_compat(cr)) for cr in coin_records]

    
    async def get_coin_records_by_hint(
            self,
            hint: bytes32,
            height_start: Optional[int] =None,
            height_end: Optional[int] =None,
            include_spent_coins: bool =False,
            page: int =1,
            timeout: Optional[int] =-1
    ) -> List[CoinRecord]:
        """Return coin records for coins hinted at.

        For info on hints see https://docs.chia.net/conditions/?_highlight=hint#hinting
        
        Arguments:
        hint -- the hint to examine

        Keyword arguments:
        height_start -- starting block height (incl)
        height_end -- ending block height (excl)
        include_spent_coins -- boolean indicating whether to include spent coins
        page -- page to be returned (if applicable)
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        self._check_heights(height_start, height_end)

        params = {
            "start_height": height_start,
            "end_height": height_end,
            "include_spent_coins": include_spent_coins,
            "hint": hint.hex()
        }
        if self.node_provider == NodeProvider.MOJONODE:
            params["page"] = page
        elif self.node_provider == NodeProvider.OFFICIALNODE:
            if height_start is None: params.pop("start_height")
            if height_end is None: params.pop("end_height")

        coin_records = (await self._request(POST, "get_coin_records_by_hint", params, timeout=timeout)).json()["coin_records"]

        return [CoinRecord.from_json_dict(coin_record_dict_backwards_compat(cr)) for cr in coin_records]

    
    async def get_block_record_by_height(self, height: int, timeout: Optional[int] =-1) -> BlockRecord:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        params = {"height": height}
        
        block_record = (await self._request(POST, "get_block_record_by_height", params, timeout=timeout)).json()["block_record"]

        return BlockRecord.from_json_dict(block_record)

    
    async def get_block_record(self, header_hash: bytes32, timeout: Optional[int] =-1) -> BlockRecord:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        params = {"header_hash": header_hash.hex()}

        block_record = (await self._request(POST, "get_block_record", params, timeout=timeout)).json()["block_record"]

        return BlockRecord.from_json_dict(block_record)

    
    async def get_block_records(self, height_start: int =0, height_end: int =100, timeout: Optional[int] =-1) -> List[BlockRecord]:
        """Return block records for given range of block heights.

        Note that this endpoint's return type is List[BlockRecord], whereas the official full node RPC client returns List[Dict[str, Any]].
        
        Keyword arguments:
        height_start -- starting block height (incl). This argument is required
        height_end -- ending block height (excl). This argument is required
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.timeout

        # This call requires a block height range to be provided
        if height_start is None or height_end is None:
            raise ValueError("Starting and ending block heights must be provided (cannot be None)")
        
        self._check_heights(height_start, height_end)
    
        params = {"start": height_start, "end": height_end}

        block_records = (await self._request(POST, "get_block_records", params, timeout=timeout)).json()["block_records"]

        return [BlockRecord.from_json_dict(br) for br in block_records]

    
    async def get_block(self, header_hash: bytes32, timeout: Optional[int] =-1) -> FullBlock:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        params = {"header_hash": header_hash.hex()}
        
        block = (await self._request(POST, "get_block", params, timeout=timeout)).json()["block"]

        return FullBlock.from_json_dict(block)

    
    async def get_blocks(self, height_start: int, height_end: int, timeout: Optional[int] =-1) -> List[FullBlock]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        if height_start is None or height_end is None:
            raise ValueError("Starting and ending block heights must be provided (cannot be None)")

        self._check_heights(height_start, height_end)

        params = {"start": height_start, "end": height_end}

        blocks = (await self._request(POST, "get_blocks", params, timeout=timeout)).json()["blocks"]

        return [FullBlock.from_json_dict(b) for b in blocks]

        
    async def get_additions_and_removals(self, header_hash: bytes32, timeout: Optional[int] =-1) -> Tuple[List[CoinRecord], List[CoinRecord]]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        params = {"header_hash": header_hash.hex()}

        response = (await self._request(POST, "get_additions_and_removals", params, timeout=timeout)).json()

        additions = []
        removals = []
        for coin_record in response["additions"]:
            additions.append(CoinRecord.from_json_dict(coin_record_dict_backwards_compat(coin_record)))
        for coin_record in response["removals"]:
            removals.append(CoinRecord.from_json_dict(coin_record_dict_backwards_compat(coin_record)))

        return additions, removals

    
    async def get_block_count_metrics(self, timeout: Optional[int] =-1) -> Dict[str, int]:
        """Return block count metrics

        This call tends to take longer than the other ones. It may be necessary to use a timeout greater than the default.

        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.timeout

        if self.node_provider == NodeProvider.OFFICIALNODE:
            return (await self._request(POST, "get_block_count_metrics", {}, timeout=timeout)).json()["metrics"]
        else:
            raise ValueError(f"Endpoint get_block_count_metrics not supported by node provider ({self.node_provider})")
    
    
    async def get_blockchain_state(self, timeout: Optional[int] =-1) -> Dict[str, Any]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        blockchain_state = (await self._request(POST, "get_blockchain_state", {}, timeout=timeout)).json()["blockchain_state"]

        if blockchain_state["peak"] is not None:
            blockchain_state["peak"] = BlockRecord.from_json_dict(blockchain_state["peak"])
        return cast(Dict[str, Any], blockchain_state)

    
    async def get_puzzle_and_solution(self, coin_id: bytes32, height_spent: Optional[int] =None, timeout: Optional[int] =-1) -> CoinSpend:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        # Mojonode doesn't require the height at which the coin was spent as a parameter
        params = {"coin_id": coin_id.hex()}
        
        # Check that height is provided if we are not using Mojonode
        if not self.node_provider == NodeProvider.MOJONODE:
            if height_spent is None:
                raise ValueError("Must provide height at which coin was spent")
            elif not height_spent >= 0:
                raise ValueError("Must provide a height at which coin was spent greater than or equal to 0")
            else:
                params["height"] = height_spent
            
        coin_spend = (await self._request(POST, "get_puzzle_and_solution", params, timeout=timeout)).json()["coin_solution"]

        return CoinSpend.from_json_dict(coin_spend)

    
    async def get_block_spends(self, header_hash: bytes32, timeout: Optional[int] =-1) -> List[CoinSpend]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        params = {"header_hash": header_hash.hex()}
        
        block_spends = (await self._request(POST, "get_block_spends", params, timeout=timeout)).json()["block_spends"]

        return [CoinSpend.from_json_dict(bs) for bs in block_spends]

    
    async def get_all_mempool_items(self, timeout: Optional[int] =-1) -> Dict[bytes32, Dict[str, Any]]:

        if timeout < 0: timeout = self.timeout
        
        if not self.node_provider == NodeProvider.OFFICIALNODE:
            raise ValueError(f"Endpoint get_all_mempool_items not supported by node provider ({self.node_provider})")
            
        mempool_items = (await self._request(POST, "get_all_mempool_items", {}, timeout=timeout)).json()["mempool_items"]

        converted: Dict[bytes32, Dict[str, Any]] = {}
        for tx_id_hex, item in mempool_items.items():
            converted[hexstr_to_bytes32(tx_id_hex)] = convert_mempool_item(item)
        return converted

        
    async def get_all_mempool_tx_ids(self, timeout: Optional[int] =-1) -> List[bytes32]:

        if timeout is not None and timeout < 0: timeout = self.timeout

        tx_ids = (await self._request(POST, "get_all_mempool_tx_ids", {}, timeout=timeout)).json()["tx_ids"]

        return [hexstr_to_bytes32(tx_id_hex) for tx_id_hex in tx_ids]

    
    async def get_mempool_item_by_tx_id(self, tx_id: bytes32, include_pending: bool =False, timeout: Optional[int] =-1) -> Dict[str, Any]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        if not self.node_provider == NodeProvider.OFFICIALNODE and include_pending == True:
            raise ValueError(f"Inclusion of pending items for endpoint get_mempool_item_by_tx_id is not supported by node provider ({self.node_provider})")
        
        params = {
            "tx_id": tx_id.hex(),
            "include_pending": include_pending
        }
        mempool_item = (await self._request(POST, "get_mempool_item_by_tx_id", params, timeout=timeout)).json()["mempool_item"]

        return convert_mempool_item(mempool_item)


    async def get_initial_freeze_period(self, timeout: Optional[int] =-1) -> int:

        if timeout is not None and timeout < 0: timeout = self.timeout

        initial_freeze_end_timestamp = (await self._request(POST, "get_initial_freeze_period", {}, timeout=timeout)).json()["INITIAL_FREEZE_END_TIMESTAMP"]

        return cast(int, initial_freeze_end_timestamp)

    
    async def healthz(self, timeout: Optional[int] =-1) -> bool:

        if timeout is not None and timeout < 0: timeout = self.timeout

        return cast(bool, (await self._request(POST, "healthz", {}, timeout=timeout)).json()["success"])


    async def get_fee_estimate(
            self,
            spend_bundle: SpendBundle =None,
            cost: int =None,
            target_times: List[int] =None,
            timeout: Optional[int] =-1
    ) -> Dict[str, Any]:
        
        """Returns a fee estimate

        Either spend_bundle or cost must be provided (but not both).
        For details on transaction costs in Chia see https://chialisp.com/costs

        Keyword arguments:
        spend_bundle -- spend bundle
        cost -- cost of transaction
        target_times -- list of target durations (in seconds) for transaction inclusion
        timeout -- request timeout in seconds

        The response contains an 'estimate' field, which is a list of fee estimates corresponding to the list of target times specified.
        """

        if timeout is not None and timeout < 0: timeout = self.timeout

        # Check that target times are well-defined
        if target_times is None:
            target_times = [0]
        elif isinstance(target_times, list):
            for tt in target_times:
                if not tt >=0: raise ValueError("Target times must be greater than or equal to 0")
        else:
            TypeError("Parameter 'target_times' must be a list (or None for the default list [0])")

        params = {
            "target_times": target_times
        }

        # Check that either spend_bundle or cost is provided
        if spend_bundle is None and cost is None:
            ValueError("Must provide a value for either 'spend_bundle' or 'cost' parameter")
        elif spend_bundle is not None and cost is not None:
            ValueError("Either 'spend_bundle' or 'cost' parameter must be None")
        elif spend_bundle is not None:
            if not isinstance(spend_bundle, SpendBundle):
                TypeError("Parameter 'spend_bundle' must be a SpendBundle")
            else:
                params["spend_bundle"] = spend_bundle.to_json_dict()
        else:
            params["cost"] = cost

        # Send request
        if self.node_provider == NodeProvider.OFFICIALNODE:
            return (await self._request(POST, "get_fee_estimate", params, timeout=timeout)).json()
        else:
            raise ValueError(f"Endpoint get_fee_estimate not supported by node provider ({self.node_provider})")

        
    async def push_tx(self, spend_bundle: SpendBundle, timeout: Optional[int] =-1) -> Dict[str, Any]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        params = {"spend_bundle": spend_bundle.to_json_dict()}
        
        return await self._request(POST, "push_tx", params, timeout=timeout)

    
    async def get_network_info(self, timeout: Optional[int] =-1) -> dict:

        if timeout is not None and timeout < 0: timeout = self.timeout

        if self.node_provider == NodeProvider.OFFICIALNODE:
            response = (await self._request(POST, "get_network_info", {}, timeout=timeout)).json()
            response.pop("success")
            return response
        else:
            raise ValueError(f"Endpoint get_network_info not supported by node provider ({self.node_provider})")

        
    async def get_network_space(self, block_header_hash_start: bytes32, block_header_hash_end: bytes32, timeout: Optional[int] =-1) -> int:
        """Returns the average Chia network space between two blocks.
        
        Arguments:
        block_header_hash_start -- block header hash of starting block
        block_header_hash_end -- block header hash of ending block

        Keyword arguments:
        timeout -- request timeout in seconds

        The network space value returned is given in bytes. To get the network space in EiB, divide by 2^60
        """

        if timeout is not None and timeout < 0: timeout = self.timeout

        params = {
            "older_block_header_hash": block_header_hash_start.hex(),
            "newer_block_header_hash": block_header_hash_end.hex()
        }
        
        if self.node_provider == NodeProvider.OFFICIALNODE:
            return cast(int, (await self._request(POST, "get_network_space", params, timeout=timeout)).json()["space"])
        else:
            raise ValueError(f"Endpoint get_network_space not supported by node provider ({self.node_provider})")


    async def get_recent_signage_point_or_eos(
            self,
            signage_point_hash: Optional[bytes32] =None,
            challenge_hash: Optional[bytes32] =None,
            timeout: Optional[int] =-1
    ) -> Optional[Dict[str, Any]]:
        """Return the most recent signage point for a given signage point hash or challenge hash.
        
        Either signage_point_hash or challenge_hash needs to be provided (but not both).
        Returns None if argument passed is not recent enough and corresponding eos cannot be found in cache.

        Keyword arguments:
        signage_point_hash -- signage point hash
        challenge_hash -- challenge hash
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.timeout

        # Check that either spend_bundle or cost is provided
        if signage_point_hash is None and challenge_hash is None:
            ValueError("Must provide a value for either 'signage_point_hash' or 'challenge_hash' parameter")
        elif signage_point_hash is not None and challenge_hash is not None:
            ValueError("Either 'signage_point_hash' or 'challenge_hash' parameter must be None")
        elif signage_point_hash is not None:
            params = {"sp_hash": signage_point_hash.hex()}
        else:
            params = {"challenge_hash": challenge_hash.hex()}
        
        if self.node_provider == NodeProvider.OFFICIALNODE:
            response = (await self._request(POST, "get_recent_signage_point_or_eos", params, timeout=timeout)).json()
            if response["success"] == False or "error" in response.keys():
                return None
            elif signage_point_hash is not None:
                return {
                    "signage_point": SignangePoint.from_json_dict(response["signage_point"]),
                    "time_received": response["time_received"],
                    "reverted": response["reverted"]
                }
            else:
                return {
                    "eos": EndOfSubSlotBundle.from_json_dict(response["eos"]),
                    "time_received": response["time_received"],
                    "reverted": response["reverted"]
                }
        else:
            raise ValueError(f"Endpoint get_signage_point_or_eos not supported by node provider ({self.node_provider})")

        
    async def get_unfinished_block_headers(self, timeout: Optional[int] =-1) -> List[UnfinishedHeaderBlock]:

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        if self.node_provider == NodeProvider.OFFICIALNODE:
            headers = (await self._request(POST, "get_unfinished_block_headers", {}, timeout=timeout)).json()["headers"]
            return [UnfinishedHeaderBlock.from_json_dict(h) for h in headers]
        else:
            raise ValueError(f"Endpoint get_unfinished_block_headers not supported by node provider ({self.node_provider})")


    async def get_routes(self, timeout: Optional[int] =-1) -> List[str]:
        """Return a list of supported RPC endpoints
        
        Keyword arguments:
        timeout -- request timeout in seconds
        """

        if timeout is not None and timeout < 0: timeout = self.timeout
        
        if self.node_provider == NodeProvider.OFFICIALNODE:
            return sorted([r for r in (await self._request(POST, "get_routes", {}, timeout=timeout)).json()["routes"] if r not in UNSUPPORTED_STANDARD_ENDPOINTS])
        elif self.node_provider == NodeProvider.MOJONODE:
            return sorted(MOJONODE_STANDARD_ENDPOINTS)
