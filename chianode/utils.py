from typing import Any, Dict, Optional
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.coin_record import CoinRecord
from chia.types.spend_bundle import SpendBundle
from chia.util.byte_types import hexstr_to_bytes


def hexstr_to_bytes32(hexstr: str) -> bytes32:
    return bytes32.from_bytes(hexstr_to_bytes(hexstr))


def coin_record_dict_backwards_compat(coin_record: Dict[str, Any]) -> Dict[str, Any]:
    del coin_record["spent"]
    return coin_record


def convert_mempool_item(mempool_item: dict) -> Dict[str, Any]:

    converted_mempool_item = {
        "additions": [Coin.from_json_dict(c) for c in mempool_item["additions"]],
        "cost": mempool_item["cost"],
        "fee": mempool_item["fee"],
        "npc_result": mempool_item["npc_result"],
        "removals": [Coin.from_json_dict(c) for c in mempool_item["removals"]],
        "spend_bundle": SpendBundle.from_json_dict(mempool_item["spend_bundle"]),
        "spend_bundle_name": hexstr_to_bytes32(mempool_item["spend_bundle_name"])
    }

    if "height_added_to_mempool" in mempool_item.keys():
        converted_mempool_item["height_added_to_mempool"] = mempool_item["height_added_to_mempool"]

    return converted_mempool_item


def convert_tx(tx: dict) -> Dict[str, Any]:

    return {
        "additions": [hexstr_to_bytes32(a) for a in tx["additions"]],
        "cost": int(tx["cost"]),
        "fee": int(tx["fee"]),
        "last_state": tx["last_state"],
        "mempool_item": convert_mempool_item(tx["mempool_item"]),
        "removals": [hexstr_to_bytes32(r) for r in tx["removals"]],
        "state_updates": tx["state_updates"]
    }


def convert_uncurried_coin_spend(uncurried_coin_spend: dict) -> Dict[str, Any]:

    converted_uncurried_coin_spend = {
        "puzzle": {
            "curried_args": uncurried_coin_spend["puzzle"]["a"], # list of curried args
            "mod_hash": hexstr_to_bytes32(uncurried_coin_spend["puzzle"]["m"]) # mod hash of uncurried puzzle
        },
        "solution": Program.to(uncurried_coin_spend["solution"])
    }
     
    return converted_uncurried_coin_spend


def convert_coin_transactions(coin_transactions: Dict[str, Optional[str]]) -> Dict[str, Optional[bytes32]]:

    converted_coin_transactions = {}

    if "added_by" in coin_transactions.keys():
        if coin_transactions["added_by"] is None:
            converted_coin_transactions["added_by"] = None
        else:
            converted_coin_transactions["added_by"] = hexstr_to_bytes32(coin_transactions["added_by"])

    if "removed_by" in coin_transactions.keys():
        if coin_transactions["removed_by"] is None:
            converted_coin_transactions["removed_by"] = None
        else:
            converted_coin_transactions["removed_by"] = hexstr_to_bytes32(coin_transactions["removed_by"])
        
    return converted_coin_transactions
