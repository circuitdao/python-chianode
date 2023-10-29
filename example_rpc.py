import asyncio
from pprint import pprint

from chianode.mojoclient import MojoClient
from chianode.utils import hexstr_to_bytes32


async def main():

    mojonode = MojoClient()

    coin_ids = [
        hexstr_to_bytes32("0x79219a5e3824001e6b2af78201c97bfee867ca21466a9647dfd32ff84e10fd96"),
        hexstr_to_bytes32("0x5a43c5bdeb0de9bd64718b83638bf721505601631ceb71d844cdddb5a56f78d7"),
        hexstr_to_bytes32("0x33830f99fd02d24712fbc593e455678cfdded40c2dd7c60583231506acd2ad4a")
    ]
    
    coin_records = await mojonode.get_coin_records_by_names(coin_ids, include_spent_coins=True)

    pprint([cr.to_json_dict() for cr in coin_records])


if __name__ == "__main__":
    asyncio.run(main())
