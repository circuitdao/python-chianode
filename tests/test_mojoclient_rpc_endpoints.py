from pytest import fixture
from conftest import GENESIS_BLOCK_HEADER_HASH
from chianode import RpcClient, MojoClient
from chia.types.blockchain_format.coin import Coin
import httpx
import hashlib


### RPC call tests ###
async def test_get_coin_record_by_name(coin_record_keys):

    coin_name = "0x9c085e5ae0e383ef13d0391283c066824af2228dadf6c8623cba1689d552804c"

    mojonode = MojoClient()
    response = await mojonode.get_coin_record_by_name(coin_name)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(coin_record_keys).issubset(set(response_json["coin_record"].keys())), "Missing key(s) in coin record"
    assert response_json["coin_record"]["confirmed_block_index"] == 395182, "Incorrect confirmed block index"
    assert response_json["coin_record"]["spent_block_index"] == 400000, "Incorrect spent block index"
    assert response_json["coin_record"]["coin"]["puzzle_hash"] == "0x997a541493e903cab06be45b375afe2392f7e12d26777e66ab6b58151084a78e", "Incorrect puzzle hash"


async def test_get_coin_records_by_names(coin_record_keys):

    # Test 1
    height_start = 395182
    height_end = 395183
    coin_name_1 = "0x9c085e5ae0e383ef13d0391283c066824af2228dadf6c8623cba1689d552804c"

    mojonode = MojoClient()
    response = await mojonode.get_coin_records_by_names([coin_name_1], height_start, height_end, True, 1)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(coin_record_keys).issubset(set(response_json["coin_records"][0].keys())), "Missing key(s) in coin record"
    assert response_json["coin_records"][0]["confirmed_block_index"] == 395182, "Incorrect confirmed block index"
    assert response_json["coin_records"][0]["coin"]["puzzle_hash"] == "0x997a541493e903cab06be45b375afe2392f7e12d26777e66ab6b58151084a78e", "Incorrect puzzle hash"

    # Test 2
    height_start = 3999951
    height_end = 4000051
    coin_name_1 = "0x79219a5e3824001e6b2af78201c97bfee867ca21466a9647dfd32ff84e10fd96" # BH 4000001
    coin_name_2 = "0x5a43c5bdeb0de9bd64718b83638bf721505601631ceb71d844cdddb5a56f78d7" # BH 3999951
    coin_name_3 = "0x33830f99fd02d24712fbc593e455678cfdded40c2dd7c60583231506acd2ad4a" # BH 4000051

    response = await mojonode.get_coin_records_by_names([coin_name_1, coin_name_2, coin_name_3], height_start, height_end, True, 1)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) <= 2, "Unexpected coin record(s) returned"
    assert len(response_json["coin_records"]) >= 2, "Missing coin record(s)"
    coin_records = sorted(response_json["coin_records"], key=lambda x: Coin.from_json_dict(x["coin"]).name())
    for r in coin_records:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"
    assert coin_records[0]["confirmed_block_index"] == 3999951, "Incorrect confirmed block index"
    assert coin_records[0]["coin"]["puzzle_hash"] == "0x5abba4dba8308b91fb3be18e04aa5c1d8a7ba957ce69b0344bf38a1f12f10ce2", "Incorrect puzzle hash"
    assert coin_records[1]["confirmed_block_index"] == 4000001, "Incorrect confirmed block index"
    assert coin_records[1]["coin"]["puzzle_hash"] == "0x9cff0b9843dc48b249871af369262b2ffa7ceda7bc4da7e14a00613c518b7dae", "Incorrect puzzle hash"

    # Test 3
    height_start = 3999952
    height_end = 4000052

    response = await mojonode.get_coin_records_by_names([coin_name_1, coin_name_2, coin_name_3], height_start, height_end, True, 1)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) <= 2, "Unexpected coin record(s) returned"
    assert len(response_json["coin_records"]) >= 2, "Missing coin record(s)"
    coin_records = sorted(response_json["coin_records"], key=lambda x: Coin.from_json_dict(x["coin"]).name())
    for r in coin_records:
        assert set(coin_record_keys).issubset(r.keys()), "Missing key(s) in coin record"
    assert coin_records[0]["confirmed_block_index"] == 4000051, "Incorrect confirmed block index"
    assert coin_records[0]["coin"]["puzzle_hash"] == "0x9fbde16e03f55c85ecf94cb226083fcfe2737d4e629a981e5db3ea0eb9907af4", "Incorrect puzzle hash"
    assert coin_records[1]["confirmed_block_index"] == 4000001, "Incorrect confirmed block index"
    assert coin_records[1]["coin"]["puzzle_hash"] == "0x9cff0b9843dc48b249871af369262b2ffa7ceda7bc4da7e14a00613c518b7dae", "Incorrect puzzle hash"


async def test_get_coin_records_by_parent_ids(coin_record_keys):

    mojonode = MojoClient(mojo_timeout=None)
    
    height_start = None
    height_end = None
    parent_ids = ["0x74acdbfea0d95404526ebc243f7be70b84192ba9237ee0948fc2bc42e5d324a5",
                  "0x453271a545ff4b2b5ff9970f663861791d2ab0e3348c491002b733d50ec9f042",
                  "0x914866872be973b816ff8f341b79b1c05e690b4d414b20e5744ad403cb665f6a"]

    # Test 1
    page = 1

    response = await mojonode.get_coin_records_by_parent_ids(parent_ids, height_start, height_end, True, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 50, "Missing coin records"
    assert len(response_json["coin_records"]) <= 50, "Coin records page exceeds 50 items"
    for r in response_json["coin_records"]:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"
        
    # Test 5
    page = 5
    
    response = await mojonode.get_coin_records_by_parent_ids(parent_ids, height_start, height_end, True, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 1, "Missing coin records"
    assert len(response_json["coin_records"]) <= 1, "Coin records page exceeds 1 item"
    assert set(coin_record_keys).issubset(set(response_json["coin_records"][0].keys())), "Missing key(s) in coin record"

        
async def test_get_coin_records_by_puzzle_hash(coin_record_keys):

    mojonode = MojoClient()
    
    height_start = None
    height_end = None
    include_spent_coins = False
    puzzle_hash = "0xf9cd704e2aace4203e17ed600bfc9fd20f475671e30d41cae912090febf16c20"

    # Test 1
    page = 1

    response = await mojonode.get_coin_records_by_puzzle_hash(puzzle_hash, height_start, height_end, include_spent_coins, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 50, "Missing coin record(s)"
    assert len(response_json["coin_records"]) <= 50, "Unexpected coin record(s) returned"
    coin_records = sorted(response_json["coin_records"], key=lambda x: Coin.from_json_dict(x["coin"]).name())
    for r in coin_records:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"
    
    # Test 2
    page = 3

    response = await mojonode.get_coin_records_by_puzzle_hash(puzzle_hash, height_start, height_end, include_spent_coins, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 24, "Missing coin record(s)"
    assert len(response_json["coin_records"]) <= 24, "Unexpected coin record(s) returned"
    coin_records = sorted(response_json["coin_records"], key=lambda x: Coin.from_json_dict(x["coin"]).name())
    for r in coin_records:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"
    

async def test_get_coin_records_by_puzzle_hashes(coin_record_keys):

    mojonode = MojoClient()
    
    height_start = None
    height_end = None
    puzzle_hashes = ["0xf9cd704e2aace4203e17ed600bfc9fd20f475671e30d41cae912090febf16c20", "0833a81b2b85b4bdb2f1b2dbca0386636d3485cc5605a80433e3a2c2fdaa0f5a"]

    # Test 1
    page = 1    
    response = await mojonode.get_coin_records_by_puzzle_hashes(puzzle_hashes, height_start, height_end, True, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 50, "Missing coin record(s)"
    assert len(response_json["coin_records"]) <= 50, "Unexpected coin record(s) returned"
    for r in response_json["coin_records"]:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"

    # Test 2
    page = 2
    response = await mojonode.get_coin_records_by_puzzle_hashes(puzzle_hashes, height_start, height_end, True, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 50, "Missing coin record(s)"
    assert len(response_json["coin_records"]) <= 50, "Unexpected coin record(s) returned"
    for r in response_json["coin_records"]:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"

    # Test 3
    page = 3
    response = await mojonode.get_coin_records_by_puzzle_hashes(puzzle_hashes, height_start, height_end, True, page)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 38, "Missing coin record(s)"
    assert len(response_json["coin_records"]) <= 38, "Unexpected coin record(s) returned"
    for r in response_json["coin_records"]:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"


async def test_get_coin_records_by_hint(coin_record_keys):

    mojonode = MojoClient(mojo_timeout=None)
    
    height_start = None #400000
    height_end = None #1900000
    include_spent_coins = True
    hint = "0x6916079cc35f377e96fa34af87d14f58ce1f08d864f93e89bbdd04a26f591540"

    response = await mojonode.get_coin_records_by_hint(hint, height_start, height_end, include_spent_coins, 1)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["coin_records"]) >= 3, "Missing coin record(s)"
    assert len(response_json["coin_records"]) <= 3, "Unexpected coin record(s) returned"
    coin_records = sorted(response_json["coin_records"], key=lambda x: Coin.from_json_dict(x["coin"]).name())
    for r in coin_records:
        assert set(coin_record_keys).issubset(set(r.keys())), "Missing key(s) in coin record"
    assert coin_records[0]["timestamp"] == 1650620445, "Incorrect timestamp"
    assert coin_records[1]["timestamp"] == 1650533680, "Incorrect timestamp"
    assert coin_records[1]["coin"]["puzzle_hash"] == "0xd229b55df95852e99f1c2708a7248380676ead58fd6a3cbfb44c870204506751", "Incorrect puzzle hash"
    assert coin_records[2]["timestamp"] == 1679530148, "Incorrect timestamp"
    assert coin_records[2]["confirmed_block_index"] == 3416908, "Incorrect confirmed block index"

    
async def test_get_block_record_by_height(block_record_keys):

    block_height = 4000000

    mojonode = MojoClient()
    response = await mojonode.get_block_record_by_height(block_height)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_record_keys).issubset(set(response_json["block_record"].keys())), "Missing key(s) in block record"
    assert response_json["block_record"]["height"] == block_height, "Incorrect block height"


async def test_get_block_record(block_record_keys):

    mojonode = MojoClient()
    
    # Test 1
    header_hash = GENESIS_BLOCK_HEADER_HASH["mainnet"]

    response = await mojonode.get_block_record(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_record_keys).issubset(set(response_json["block_record"].keys())), "Missing key(s) in block record"
    assert response_json["block_record"]["height"] == 0, "Incorrect block height"
    #assert response_json["block_record"]["prev_transaction_block_height"] == 0, "Incorrect previous transaction block height"
    assert response_json["block_record"]["farmer_puzzle_hash"] == "0x3d8765d3a597ec1d99663f6c9816d915b9f68613ac94009884c4addaefcce6af", "Incorrect farmer puzzle hash"
    assert response_json["block_record"]["signage_point_index"] == 2, "Incorrect signage point index"

    # Test 2
    header_hash = "0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d"

    response = await mojonode.get_block_record(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_record_keys).issubset(set(response_json["block_record"].keys())), "Missing key(s) in block record"
    assert response_json["block_record"]["height"] == 4030597, "Incorrect block height"
    assert response_json["block_record"]["prev_transaction_block_height"] == 4030594, "Incorrect previous transaction block height"
    assert response_json["block_record"]["farmer_puzzle_hash"] == "0x907491ca39c35bc1f9a6eda33f7c0f97a9f583975088dad7216f1edd79f522ae", "Incorrect farmer puzzle hash"
    assert response_json["block_record"]["signage_point_index"] == 22, "Incorrect signage point index"


async def test_get_block_records(block_record_keys):

    mojonode = MojoClient()
    
    # Test 1
    height_start = 0
    height_end = 100

    response = await mojonode.get_block_records(height_start, height_end)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["block_records"]) >= height_end - height_start + 1, "Block record(s) missing"
    assert len(response_json["block_records"]) <= height_end - height_start + 1, "Too many block records"
    for h in range(height_start, height_end):
        assert set(block_record_keys).issubset(set(response_json["block_records"][h].keys())), "Missing key(s) in block record"
        assert response_json["block_records"][h]["height"] == h, "Incorrect block height"

    # Test 2
    height_start = 4000000
    height_end = 4000100

    response = await mojonode.get_block_records(height_start, height_end)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["block_records"]) >= height_end - height_start + 1, "Block record(s) missing"
    assert len(response_json["block_records"]) <= height_end - height_start + 1, "Too many block records"
    for h in range(len(response_json["block_records"])):
        assert set(block_record_keys).issubset(set(response_json["block_records"][h].keys())), "Missing key(s) in block record"
        assert response_json["block_records"][h]["height"] == height_start + h, "Incorrect block height"

        
async def test_get_block(block_keys, foliage_keys, foliage_block_data_keys, transactions_info_keys, reward_chain_block_keys,
                         proof_of_space_keys, vdf_keys, proof_keys, foliage_transaction_block_keys):

    mojonode = MojoClient()

    # Test 1
    header_hash = GENESIS_BLOCK_HEADER_HASH["mainnet"]
    
    response = await mojonode.get_block(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_keys).issubset(set(response_json["block"].keys())), "Missing key(s) in block"
    assert set(foliage_keys).issubset(set(response_json["block"]["foliage"].keys())), "Missing key(s) in foliage"
    assert set(foliage_block_data_keys).issubset(set(response_json["block"]["foliage"]["foliage_block_data"].keys())), "Missing key(s) in foliage block data"
    assert set(transactions_info_keys).issubset(set(response_json["block"]["transactions_info"].keys())), "Missing key(s) in transactions info"
    assert set(reward_chain_block_keys).issubset(set(response_json["block"]["reward_chain_block"].keys())), "Missing key(s) in reward chain block"
    assert set(proof_of_space_keys).issubset(set(response_json["block"]["reward_chain_block"]["proof_of_space"].keys())), "Missing key(s) in proof of space"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_ip_vdf"].keys())), "Missing key(s) in reward chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_sp_vdf"].keys())), "Missing key(s) in reward chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_ip_vdf"].keys())), "Missing key(s) in challenge chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_sp_vdf"].keys())), "Missing key(s) in challenge chain sp vdf"
    assert response_json["block"]["reward_chain_block"]["infused_challenge_chain_ip_vdf"] is None, "Infused challenge chain ip vdf is not None"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_ip_proof"].keys())), "Missing key(s) in reward chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_sp_proof"].keys())), "Missing key(s) in reward chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_ip_proof"].keys())), "Missing key(s) in challenge chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_sp_proof"].keys())), "Missing key(s) in challenge chain sp proof"
    assert response_json["block"]["infused_challenge_chain_ip_proof"] is None, "Infused challenge chain ip proof is not None"
    assert set(foliage_transaction_block_keys).issubset(set(response_json["block"]["foliage_transaction_block"].keys())), "Missing key(s) in foliage transaction block"


    # Test 2
    header_hash = "0x7357071bb77de2e98b9b1daf6b87f67dd8481fa144bcc03d331dba8664fc04f9" # BH 1 (transaction block w/o transactions)
    
    response = await mojonode.get_block(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_keys).issubset(set(response_json["block"].keys())), "Missing key(s) in block"
    assert set(foliage_keys).issubset(set(response_json["block"]["foliage"].keys())), "Missing key(s) in foliage"
    assert set(foliage_block_data_keys).issubset(set(response_json["block"]["foliage"]["foliage_block_data"].keys())), "Missing key(s) in foliage block data"
    assert set(transactions_info_keys).issubset(set(response_json["block"]["transactions_info"].keys())), "Missing key(s) in transactions info"
    assert set(reward_chain_block_keys).issubset(set(response_json["block"]["reward_chain_block"].keys())), "Missing key(s) in reward chain block"
    assert set(proof_of_space_keys).issubset(set(response_json["block"]["reward_chain_block"]["proof_of_space"].keys())), "Missing key(s) in proof of space"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_ip_vdf"].keys())), "Missing key(s) in reward chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_sp_vdf"].keys())), "Missing key(s) in reward chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_ip_vdf"].keys())), "Missing key(s) in challenge chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_sp_vdf"].keys())), "Missing key(s) in challenge chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["infused_challenge_chain_ip_vdf"].keys())), "Missing key(s) in infused challenge chain ip vdf"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_ip_proof"].keys())), "Missing key(s) in reward chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_sp_proof"].keys())), "Missing key(s) in reward chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_ip_proof"].keys())), "Missing key(s) in challenge chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_sp_proof"].keys())), "Missing key(s) in challenge chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["infused_challenge_chain_ip_proof"].keys())), "Missing key(s) in infused challenge chain ip proof"
    assert set(foliage_transaction_block_keys).issubset(set(response_json["block"]["foliage_transaction_block"].keys())), "Missing key(s) in foliage transaction block"

    # Test 3
    header_hash = "0x9ec0447c9a4f5183f3235523aacf01fefb915f5ad90e2b5f1b45894412a4fb92" # BY 4030596 (not a transaction block)
    
    response = await mojonode.get_block(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_keys).issubset(set(response_json["block"].keys())), "Missing key(s) in block"
    assert set(foliage_keys).issubset(set(response_json["block"]["foliage"].keys())), "Missing key(s) in foliage"
    assert set(foliage_block_data_keys).issubset(set(response_json["block"]["foliage"]["foliage_block_data"].keys())), "Missing key(s) in foliage block data"
    assert response_json["block"]["transactions_info"] is None, "Transactions info is not None"
    assert set(reward_chain_block_keys).issubset(set(response_json["block"]["reward_chain_block"].keys())), "Missing key(s) in reward chain block"
    assert set(proof_of_space_keys).issubset(set(response_json["block"]["reward_chain_block"]["proof_of_space"].keys())), "Missing key(s) in proof of space"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_ip_vdf"].keys())), "Missing key(s) in reward chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_sp_vdf"].keys())), "Missing key(s) in reward chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_ip_vdf"].keys())), "Missing key(s) in challenge chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_sp_vdf"].keys())), "Missing key(s) in challenge chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["infused_challenge_chain_ip_vdf"].keys())), "Missing key(s) in infused challenge chain ip vdf"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_ip_proof"].keys())), "Missing key(s) in reward chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_sp_proof"].keys())), "Missing key(s) in reward chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_ip_proof"].keys())), "Missing key(s) in challenge chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_sp_proof"].keys())), "Missing key(s) in challenge chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["infused_challenge_chain_ip_proof"].keys())), "Missing key(s) in infused challenge chain ip proof"
    assert response_json["block"]["foliage_transaction_block"] is None, "Foliage transaction block is not None"
    
    # Test 4
    header_hash = "0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d" # BH 4030597 (transaction block w/ transactions)
    
    response = await mojonode.get_block(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(block_keys).issubset(set(response_json["block"].keys())), "Missing key(s) in block"
    assert set(foliage_keys).issubset(set(response_json["block"]["foliage"].keys())), "Missing key(s) in foliage"
    assert set(foliage_block_data_keys).issubset(set(response_json["block"]["foliage"]["foliage_block_data"].keys())), "Missing key(s) in foliage block data"
    assert set(transactions_info_keys).issubset(set(response_json["block"]["transactions_info"].keys())), "Missing key(s) in transactions info"
    assert set(reward_chain_block_keys).issubset(set(response_json["block"]["reward_chain_block"].keys())), "Missing key(s) in reward chain block"
    assert set(proof_of_space_keys).issubset(set(response_json["block"]["reward_chain_block"]["proof_of_space"].keys())), "Missing key(s) in proof of space"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_ip_vdf"].keys())), "Missing key(s) in reward chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["reward_chain_sp_vdf"].keys())), "Missing key(s) in reward chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_ip_vdf"].keys())), "Missing key(s) in challenge chain ip vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["challenge_chain_sp_vdf"].keys())), "Missing key(s) in challenge chain sp vdf"
    assert set(vdf_keys).issubset(set(response_json["block"]["reward_chain_block"]["infused_challenge_chain_ip_vdf"].keys())), "Missing key(s) in infused challenge chain ip vdf"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_ip_proof"].keys())), "Missing key(s) in reward chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["reward_chain_sp_proof"].keys())), "Missing key(s) in reward chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_ip_proof"].keys())), "Missing key(s) in challenge chain ip proof"
    assert set(proof_keys).issubset(set(response_json["block"]["challenge_chain_sp_proof"].keys())), "Missing key(s) in challenge chain sp proof"
    assert set(proof_keys).issubset(set(response_json["block"]["infused_challenge_chain_ip_proof"].keys())), "Missing key(s) in infused challenge chain ip proof"
    assert set(foliage_transaction_block_keys).issubset(set(response_json["block"]["foliage_transaction_block"].keys())), "Missing key(s) in foliage transaction block"

    
async def test_get_blocks(block_keys, foliage_keys, foliage_block_data_keys, transactions_info_keys, reward_chain_block_keys,
                          proof_of_space_keys, vdf_keys, proof_keys, foliage_transaction_block_keys):

    mojonode = MojoClient()

    height_start = 4030570
    height_end = 4030620
    
    response = await mojonode.get_blocks(height_start, height_end)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    for h in range(height_end - height_start + 1):
        
        # Check whether we are dealing with a transaction block or not
        transaction_block = True
        if response_json["blocks"][h]["transactions_info"] is None:
            transaction_block = False
            
        assert set(block_keys).issubset(set(response_json["blocks"][h].keys())), "Missing key(s) in block"
        assert set(foliage_keys).issubset(set(response_json["blocks"][h]["foliage"].keys())), "Missing key(s) in foliage"
        assert set(foliage_block_data_keys).issubset(set(response_json["blocks"][h]["foliage"]["foliage_block_data"].keys())), "Missing key(s) in foliage block data"
        if transaction_block:
            assert set(transactions_info_keys).issubset(set(response_json["blocks"][h]["transactions_info"].keys())), "Missing key(s) in transactions info"
        else:
            assert response_json["blocks"][h]["transactions_info"] is None, "Transaction info is not None"
        assert set(reward_chain_block_keys).issubset(set(response_json["blocks"][h]["reward_chain_block"].keys())), "Missing key(s) in reward chain block"
        assert set(proof_of_space_keys).issubset(set(response_json["blocks"][h]["reward_chain_block"]["proof_of_space"].keys())), "Missing key(s) in proof of space"
        assert set(vdf_keys).issubset(set(response_json["blocks"][h]["reward_chain_block"]["reward_chain_ip_vdf"].keys())), "Missing key(s) in reward chain ip vdf"
        assert set(vdf_keys).issubset(set(response_json["blocks"][h]["reward_chain_block"]["reward_chain_sp_vdf"].keys())), "Missing key(s) in reward chain sp vdf"
        assert set(vdf_keys).issubset(set(response_json["blocks"][h]["reward_chain_block"]["challenge_chain_ip_vdf"].keys())), "Missing key(s) in challenge chain ip vdf"
        assert set(vdf_keys).issubset(set(response_json["blocks"][h]["reward_chain_block"]["challenge_chain_sp_vdf"].keys())), "Missing key(s) in challenge chain sp vdf"
        # Not checking infused challenge chain ip vdf
        assert set(proof_keys).issubset(set(response_json["blocks"][h]["reward_chain_ip_proof"].keys())), "Missing key(s) in reward chain ip proof"
        assert set(proof_keys).issubset(set(response_json["blocks"][h]["reward_chain_sp_proof"].keys())), "Missing key(s) in reward chain sp proof"
        assert set(proof_keys).issubset(set(response_json["blocks"][h]["challenge_chain_ip_proof"].keys())), "Missing key(s) in challenge chain ip proof"
        assert set(proof_keys).issubset(set(response_json["blocks"][h]["challenge_chain_sp_proof"].keys())), "Missing key(s) in challenge chain sp proof"
        # Not checking infused challenge chain ip proof
        if transaction_block:
            assert set(foliage_transaction_block_keys).issubset(set(response_json["blocks"][h]["foliage_transaction_block"].keys())), "Missing key(s) in foliage transaction block"
        else:
            assert response_json["blocks"][h]["foliage_transaction_block"] is None, "Missing key(s) in foliage transaction block is not None"


# Note: no test for /get_all_block as this endpoint is no longer supported

async def test_get_additions_and_removals(additions_removals_keys, coin_record_keys):

    mojonode = MojoClient()

    header_hash = "0x7357071bb77de2e98b9b1daf6b87f67dd8481fa144bcc03d331dba8664fc04f9" # BH 1 (transaction block w/o transactions)
    
    response = await mojonode.get_additions_and_removals(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(additions_removals_keys).issubset(response_json.keys()), "Missing key(s) in additions and removals"
    for c in response_json["additions"] + response_json["removals"]:
        assert set(coin_record_keys).issubset(set(c.keys())), "Missing key(s) in coin record"

        
async def test_get_blockchain_state(blockchain_state_keys, peak_keys, sync_keys):

    mojonode = MojoClient()

    response = await mojonode.get_blockchain_state()

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(blockchain_state_keys).issubset(response_json["blockchain_state"].keys()), "Missing key(s) in blockchain state"
    assert set(peak_keys).issubset(response_json["blockchain_state"]["peak"].keys()), "Missing key(s) in peak"
    assert set(sync_keys).issubset(response_json["blockchain_state"]["sync"].keys()), "Missing key(s) in sync"

    
async def test_get_puzzle_and_solution(spend_keys):

    mojonode = MojoClient()

    coin_id = "0x9e3a9d74afb7023d4f2828cb9c526052ac007f857d5bdb61b24f3356241056b8"
    height_spent = 4026436

    # Sufficient to pass coin_id only with Mojonode. Official Chia RPC requires height_spent parameter in addition
    response = await mojonode.get_puzzle_and_solution(coin_id)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(spend_keys).issubset(response_json["coin_solution"].keys()), "Missing key(s) in coin solution"
    assert response_json["coin_solution"]["coin"]["parent_coin_info"] == "0x8424de665637aff43f54f7e45c145f0d92392825792b3bfe31a721204386fb91", "Incorrect parent coin info"
    assert response_json["coin_solution"]["puzzle_reveal"] == "0xff02ffff01ff02ffff01ff02ffff03ff0bffff01ff02ffff03ffff09ff05ffff1dff0bffff1effff0bff0bffff02ff06ffff04ff02ffff04ff17ff8080808080808080ffff01ff02ff17ff2f80ffff01ff088080ff0180ffff01ff04ffff04ff04ffff04ff05ffff04ffff02ff06ffff04ff02ffff04ff17ff80808080ff80808080ffff02ff17ff2f808080ff0180ffff04ffff01ff32ff02ffff03ffff07ff0580ffff01ff0bffff0102ffff02ff06ffff04ff02ffff04ff09ff80808080ffff02ff06ffff04ff02ffff04ff0dff8080808080ffff01ff0bffff0101ff058080ff0180ff018080ffff04ffff01b085a35d9fa7068c004e3a6173cff6f6cb4c9e1d6e03de0ef43096a2170d0d6ae0382f83a833d61797964c20bb38d3bb2aff018080", "Incorrect puzzle reveal"
    assert response_json["coin_solution"]["solution"] == "0xff80ffff01ffff33ffa00833a81b2b85b4bdb2f1b2dbca0386636d3485cc5605a80433e3a2c2fdaa0f5aff0180ffff33ffa0fa48420eba0456dd5128e359cf57ee7a9d10556d84aaf4ef05f245c78717ee3dff8600e8d449827f80ffff34ff835b8d8080ffff3cffa02db46db081105e8ba47e43abf570668090057f42f302a3ff3f25a11ab012fd9c8080ff8080", "Incorrect solution"

    
async def test_get_block_spends(spend_keys):

    mojonode = MojoClient()

    header_hash = "0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d"
    
    response = await mojonode.get_block_spends(header_hash)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["block_spends"]) >= 8, "Missing block spend(s)"
    assert len(response_json["block_spends"]) <= 8, "Unexpected block spend(s)"
    for s in range(len(response_json["block_spends"])):
        assert set(spend_keys).issubset(response_json["block_spends"][s].keys()), "Missing key(s) in block spend"


async def test_get_all_mempool_tx_ids():

    mojonode = MojoClient()

    response = await mojonode.get_all_mempool_tx_ids()

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert "tx_ids" in set(response_json.keys()), "Missing key(s) in all mempool tx ids"


async def test_get_mempool_item_by_tx_id(mempool_item_keys, npc_result_keys, conds_keys, spend_bundle_keys):

    mojonode = MojoClient()

    # First, pick an item from the mempool
    tx_id = ""
    while tx_id == "":
        response = await mojonode.get_all_mempool_tx_ids()
        response_json = response.json()
        if response_json["tx_ids"]:
            tx_id = response_json["tx_ids"][0]
        else:
            asyncio.sleep(3)

    # Once we've picked a mempool item, get the details
    response = await mojonode.get_mempool_item_by_tx_id(tx_id)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert set(mempool_item_keys).issubset(set(response_json["mempool_item"].keys())), "Missing key(s) in mempool item"
    # TODO: Check mempool items (see fixtures)


async def test_get_initial_freeze_period():

    mojonode = MojoClient()

    response = await mojonode.get_initial_freeze_period()

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert response_json["INITIAL_FREEZE_END_TIMESTAMP"] == 1620061200, "INITIAL_FREE_END_TIMESTAMP does not match"


async def test_healthz():

    mojonode = MojoClient()

    response = await mojonode.healthz()

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert response_json["success"] == True, "Not healthy"


async def test_get_routes():

    mojonode = MojoClient()

    response = await mojonode.get_routes()

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"
    assert len(response_json["routes"]) >= 27, "Missing routes"
    assert len(response_json["routes"]) <= 27, "Unknown route returned"
