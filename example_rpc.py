import asyncio
from chianode.mojoclient import MojoClient
from pprint import pprint

async def main():

    mojonode = MojoClient()

    coin_ids = [
        "0x79219a5e3824001e6b2af78201c97bfee867ca21466a9647dfd32ff84e10fd96",
        "0x5a43c5bdeb0de9bd64718b83638bf721505601631ceb71d844cdddb5a56f78d7",
        "0x33830f99fd02d24712fbc593e455678cfdded40c2dd7c60583231506acd2ad4a"
    ]
    
    response = await mojonode.get_coin_records_by_names(coin_ids, include_spent_coins=True)

    response.raise_for_status()
    pprint(response.json())

if __name__ == "__main__":
    asyncio.run(main())
