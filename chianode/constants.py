import os.path

GET = "GET"
POST = "POST"

CHIA_DIRECTORY = os.path.expanduser("~/.chia")

MAINNET = "mainnet"
TESTNET10 = "testnet10"

LOCALHOST = "https://localhost:8555/"
MOJONODE = "https://api.mojonode.com/"

MOJONODE_EVENT_OBJECTS = ["coin", "block", "transaction"]
MOJONODE_PAGE_SIZE = 50
MOJONODE_MAX_HEIGHT_DIFF = 100
MOJONODE_RPC_ENDPOINTS = [
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
