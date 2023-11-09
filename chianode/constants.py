from enum import Enum

NEWLINE = "\n"

GET = "GET"
POST = "POST"

class Network(Enum):
    MAINNET = 1
    TESTNET10 = 2
    SIMULATOR0 = 3

class NodeProvider(Enum):
    FULLNODE = 1
    MOJONODE = 2 

    def base_url(self) -> str:
        if self.name == "FULLNODE":
            return "https://localhost"
        elif self.name == "MOJONODE":
            return "https://api.mojonode.com"
        else:
            raise ValueError(f"Base URL for {self.name} not defined")

MOJONODE_EVENT_OBJECTS = ["coin", "block", "transaction"]
MOJONODE_PAGE_SIZE = 50
MOJONODE_MAX_HEIGHT_DIFF = 100
MOJONODE_STANDARD_ENDPOINTS = [
    "/get_coin_record_by_name",
    "/get_coin_records_by_name",
    "/get_coin_records_by_parent_ids",
    "/get_coin_records_by_puzzle_hash",
    "/get_coin_records_by_puzzle_hashes",
    "/get_coin_records_by_hint",
    "/get_block_record_by_height",
    "/get_block_record",
    "/get_block_records",
    "/get_block",
    "/get_blocks",
    "/get_additions_and_removals",
    "/get_blockchain_state",
    "/get_puzzle_and_solution",
    "/get_block_spends",
    "/get_all_mempool_tx_ids",
    "/get_mempool_item_by_tx_id",
    "/get_initial_freeze_period",
    "/healthz",
    "/push_tx"
]
MOJONODE_NONSTANDARD_ENDPOINTS = [
    "/get_tx_by_name",
    "/get_uncurried_coin_spend",
    "/get_transactions_for_coin",
    "/get_query_schema",
    "/query",
    "/events",
    "/get_latest_singleton_spend"
]
UNSUPPORTED_STANDARD_ENDPOINTS = [
    "/get_connections",
    "/open_connection",
    "/close_connection",
    "/stop_node"
]
