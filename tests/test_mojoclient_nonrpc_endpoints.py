from pytest import fixture
from chianode import RpcClient, MojoClient
import httpx


### Mojonode-specific endpoints ###
async def test_get_tx_by_name(transaction_keys, mempool_item_keys):

    mojonode = MojoClient()

    tx_id = "96753379426f0e0d9f35d40f6fc84473dd5a6a6dc531d26ab414d6b348f8d0d6"

    response = await mojonode.get_tx_by_name(tx_id)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(transaction_keys).issubset(set(response_json["transaction"].keys())), "Missing key(s) in mempool transaction"
    assert set(mempool_item_keys).issubset(set(response_json["transaction"]["mempool_item"].keys())), "Missing key(s) in mempool item"
    # TODO: Test mempool items (see fixtures)

async def test_get_uncurried_coin_spend():

    mojonode = MojoClient()

    coin_id = "0x9e3a9d74afb7023d4f2828cb9c526052ac007f857d5bdb61b24f3356241056b8"

    response = await mojonode.get_uncurried_coin_spend(coin_id)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    # TODO: add further tests
    
async def test_get_transactions_for_coin():

    mojonode = MojoClient(mojo_timeout=None)

    #coin_id = "0x2ca75063ff8753a84fd24ba9e980c473c411119bec04373ea63ef326e8e8a1ee" # -> has added by = null
    coin_id = "0xdbae6e3db31db2ee4a6def68708de334d33348cdf29b6dbc632d04bb89eb0b2f" # -> has added by and removed by = null

    response = await mojonode.get_transactions_for_coin(coin_id)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    # TODO: some more asserts

async def test_get_query_schema(query_schema_keys, table_names):

    mojonode = MojoClient()

    response = await mojonode.get_query_schema()

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, list), "Response body not a list (or missing)"
    for t in response_json:
        assert set(query_schema_keys).issubset(set(t.keys())), "Missing key(s) in schema"
        assert set(table_names).issubset(set([t["name"] for t in response_json])), "Missing table name(s)"

async def test_query_coin_records(query_keys, coin_records_columns):

    mojonode = MojoClient(mojo_timeout=None)

    query = "SELECT * FROM coin_records WHERE confirmed_block_height = 4000001"
    
    response = await mojonode.query(query)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(query_keys).issubset(response_json.keys()), "Missing key(s) in query response"
    assert response_json["status"] == "finished", "Status is not 'finished'"
    assert response_json["errors"] is None, "Errors is not None"
    assert set(coin_records_columns).issubset(response_json["data"].keys()), "Column(s) missing in coin_records table"
    assert len(response_json["data"]["name"]) >= 112, "Coin record(s) missing in coin_records table"
    assert len(response_json["data"]["name"]) <= 112, "Unexpected coin record(s) returned from coin_records table"

async def test_query_block_records_1(query_keys, block_records_columns):

    mojonode = MojoClient(mojo_timeout=None)
    
    query = "SELECT * FROM block_records WHERE height = 4000001"
    
    response = await mojonode.query(query)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(query_keys).issubset(response_json.keys()), "Missing key(s) in query response"
    assert response_json["status"] == "finished", "Status is not 'finished'"
    assert response_json["errors"] is None, "Errors is not None"
    assert set(block_records_columns).issubset(response_json["data"].keys()), "Column(s) missing in block_records table"
    assert response_json["data"]["weight"][0] == "8263665968", "Incorrect weight in block_records table"
    assert response_json["data"]["cost"][0] == "2227382265", "Incorrect cost returned from block_records table"

async def test_query_block_records_2(query_keys, block_records_columns):

    mojonode = MojoClient(mojo_timeout=None)
    
    query = "SELECT * FROM block_records WHERE height = 4000001 OR height = 300004 OR height = 2500000 ORDER BY height ASC"
    
    response = await mojonode.query(query)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(query_keys).issubset(response_json.keys()), "Missing key(s) in query response"
    assert response_json["status"] == "finished", "Status is not 'finished'"
    assert response_json["errors"] is None, "Errors is not None"
    assert set(block_records_columns).issubset(response_json["data"].keys()), "Column(s) missing in block_records table"
    assert response_json["data"]["hash"][0] == "0x45fd27a2f7d2accbef7886e7a8ff0d4fab5604013590db7a6524738f3969dabe", "Incorrect block hash"
    assert response_json["data"]["hash"][1] == "0x9d50f04663b198fd397b9620584121dbeb31a98a792786e5acc43a63c470ce41", "Incorrect block hash"
    assert response_json["data"]["hash"][2] == "0x4f982a6b947a50d9346420b3b7c1bda7b79e766ae3767b1af4b09e515e12bf14", "Incorrect block hash"
    assert response_json["data"]["weight"][2] == "8263665968", "Incorrect weight in block_records table"
    assert response_json["data"]["cost"][2] == "2227382265", "Incorrect cost returned from block_records table"
    assert response_json["data"]["aggregated_signature"][1] == None, "Aggregated signature not None"
    assert response_json["data"]["aggregated_signature"][2] == "0x8cced0b050bfb25403dacb9417ab556f28bbe17c0d2c91a9c81a3b1b549e95ba93130fde0703c62da0f0a13e3c7dc43216d3495a231d000f751954360ae2221f85a6f3955401fa6058eb3f900d87c88bbcfa1076ed89836e265f45c3ad8bd0de", "Incorrect aggregated signature"

async def test_query_transactions(query_keys, transactions_columns):

    mojonode = MojoClient(mojo_timeout=None)

    tx_id_1 = "0x33d7a50d8daef448b542f59cdc9675934817c632aa477f31a4291f7fd3a4231d"
    tx_id_2 = "0x4bdf56ada01ce22ca0d3e9eb23c42b95a5cfb9003d59e3ac87b48b20aaa1f5c5"

    query = f"SELECT * FROM transactions WHERE name = '{tx_id_1}' or name = '{tx_id_2}' ORDER BY created_at ASC"
    
    response = await mojonode.query(query)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(query_keys).issubset(response_json.keys()), "Missing key(s) in query response"
    assert response_json["status"] == "finished", "Status is not 'finished'"
    assert response_json["errors"] is None, "Errors is not None"
    assert set(transactions_columns).issubset(response_json["data"].keys()), "Column(s) missing in transactions table"
    assert response_json["data"]["added_at_height"][0] == 3374085, "Incorrect added_at_height value"
    assert response_json["data"]["aggregated_signature"][1] == "0xa91513cc445bf2fece7948a0899d683092c7e5a65a225766f9d0efeb4a46ae1cd020c6e082585cde76afece835f0ad5b012271502e4864f0ebb21a8854e3f3a505cc0ec55806498517bbdcbf02a1347c4539c4dd74a1b1a6d0a9bd839ebc2f47", "Incorrect aggreagted signature"


async def test_get_latest_singleton_spend(latest_singleton_spend_keys, latest_spend_keys, current_coin_keys):
    
    mojonode = MojoClient(mojo_timeout=None)

    address = "nft1vx8rmm0d50e4vlthkrqppskyeccqrmknevqutnt2y9mvhwfckvssd5d6py"
    
    response = await mojonode.get_latest_singleton_spend(address)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(latest_singleton_spend_keys).issubset(set(response_json.keys())), "Missing key(s) in latest singleton spend"
    assert set(latest_spend_keys).issubset(set(response_json["latest_spend"].keys())), "Missing key(s) in latest spend"
    assert set(current_coin_keys).issubset(set(response_json["current_coin"].keys())), "Missing key(s) in current coin"
    assert response_json["latest_spend"]["coin"]["parent_coin_info"] == "0x3bbd581d98e55c8a8dad5e3af506721c589130fb71676f4e31a8a94d124c8020", "Parent coin ID does not match"
    assert response_json["latest_spend"]["coin"]["puzzle_hash"] == "0xddfea422c712af51dcaf9e79994a0a0c29dd14cf7d6f4f4190fe6177356614ce", "Puzzle hash does not match"
    assert response_json["latest_spend"]["solution"] == "0xffffa02c3981168f853ba651fe3735395797580a8b75e9dfb6c48c04cb8e86e19fd8d8ffa0115f30e11f8c915bacdd8749bf55d311654ae14c0786edc8ea9d7bddb7fceaacff0180ff01ffffffff80ffff01ffff81f6ffa0ee426f4d28be00e4a55e617c64e0f5f11206a435749f6b10888ca36adffe75edff80ffa0a2b76656f5ecebc91909351a7df386e9aa3da665cb5bd8611534901ce991a5c080ffff33ffa0c4d070e361f4950ae71f0b3c1a38ca7937d0d4710309b7ed1406555d692abde9ff01ffffa0c4d070e361f4950ae71f0b3c1a38ca7937d0d4710309b7ed1406555d692abde9808080ff8080808080", "Solution does not match"
    assert response_json["current_coin"]["coin"]["parent_coin_info"] == "0x6dc73fa502eed08fe4d9aa65ef66b16c9fb1cebe5d1340465808309ac3d23836", "Parent coin ID does not match"
    assert response_json["current_coin"]["coin"]["puzzle_hash"] == "0xa225a915d96e7a6660f17231171e3541b6243b5445002600378bc056ac520ca0", "Puzzle hash does not match"
    assert response_json["current_coin"]["confirmed_block_index"] == 3521926, "Confirmed block index incorrect"
    assert response_json["current_coin"]["timestamp"] == 1681494253, "Timestamp incorrect"
