from pytest import fixture
from tests.conftest import NODE_PROVIDER, GENESIS_BLOCK_HEADER_HASH, get_client

from typing import Any, Dict, List, Optional, Tuple

from chia.consensus.block_record import BlockRecord
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.serialized_program import SerializedProgram
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_record import CoinRecord
from chia.types.coin_spend import CoinSpend
from chia.types.full_block import FullBlock

from chianode.utils import hexstr_to_bytes32
from chianode.constants import NodeProvider


### Standard endpoints ###
async def test_get_coin_record_by_name():

    coin_name = hexstr_to_bytes32("0x9c085e5ae0e383ef13d0391283c066824af2228dadf6c8623cba1689d552804c")

    node = get_client(NODE_PROVIDER)
    
    response = await node.get_coin_record_by_name(coin_name)

    assert isinstance(response, CoinRecord), "Response not a CoinRecord (or missing)"
    assert response.confirmed_block_index == 395182, "Incorrect confirmed block index"
    assert response.spent_block_index == 400000, "Incorrect spent block index"
    assert response.coin.puzzle_hash == hexstr_to_bytes32("0x997a541493e903cab06be45b375afe2392f7e12d26777e66ab6b58151084a78e"), "Incorrect puzzle hash"


async def test_get_coin_records_by_names():

    # Test 1
    height_start = 395182
    height_end = 395183
    coin_name_1 = hexstr_to_bytes32("0x9c085e5ae0e383ef13d0391283c066824af2228dadf6c8623cba1689d552804c")

    node = get_client(NODE_PROVIDER)
    
    response = await node.get_coin_records_by_names([coin_name_1], height_start, height_end, True, 1)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert response[0].confirmed_block_index == 395182, "Incorrect confirmed block index"
    assert response[0].coin.puzzle_hash == hexstr_to_bytes32("0x997a541493e903cab06be45b375afe2392f7e12d26777e66ab6b58151084a78e"), "Incorrect puzzle hash"

    # Test 2
    height_start = 3999951
    height_end = 4000051
    coin_name_1 = hexstr_to_bytes32("0x79219a5e3824001e6b2af78201c97bfee867ca21466a9647dfd32ff84e10fd96") # BH 4000001
    coin_name_2 = hexstr_to_bytes32("0x5a43c5bdeb0de9bd64718b83638bf721505601631ceb71d844cdddb5a56f78d7") # BH 3999951
    coin_name_3 = hexstr_to_bytes32("0x33830f99fd02d24712fbc593e455678cfdded40c2dd7c60583231506acd2ad4a") # BH 4000051

    response = await node.get_coin_records_by_names([coin_name_1, coin_name_2, coin_name_3], height_start, height_end, True, 1)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert len(response) <= 2, "Unexpected coin record(s) returned"
    assert len(response) >= 2, "Missing coin record(s)"
    coin_records = sorted(response, key=lambda x: x.coin.name())
    assert coin_records[0].confirmed_block_index == 3999951, "Incorrect confirmed block index"
    assert coin_records[0].coin.puzzle_hash == hexstr_to_bytes32("0x5abba4dba8308b91fb3be18e04aa5c1d8a7ba957ce69b0344bf38a1f12f10ce2"), "Incorrect puzzle hash"
    assert coin_records[1].confirmed_block_index == 4000001, "Incorrect confirmed block index"
    assert coin_records[1].coin.puzzle_hash == hexstr_to_bytes32("0x9cff0b9843dc48b249871af369262b2ffa7ceda7bc4da7e14a00613c518b7dae"), "Incorrect puzzle hash"

    # Test 3
    height_start = 3999952
    height_end = 4000052

    response = await node.get_coin_records_by_names([coin_name_1, coin_name_2, coin_name_3], height_start, height_end, True, 1)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert len(response) <= 2, "Unexpected coin record(s) returned"
    assert len(response) >= 2, "Missing coin record(s)"
    coin_records = sorted(response, key=lambda x: x.coin.name())
    assert coin_records[0].confirmed_block_index == 4000051, "Incorrect confirmed block index"
    assert coin_records[0].coin.puzzle_hash == hexstr_to_bytes32("0x9fbde16e03f55c85ecf94cb226083fcfe2737d4e629a981e5db3ea0eb9907af4"), "Incorrect puzzle hash"
    assert coin_records[1].confirmed_block_index == 4000001, "Incorrect confirmed block index"
    assert coin_records[1].coin.puzzle_hash == hexstr_to_bytes32("0x9cff0b9843dc48b249871af369262b2ffa7ceda7bc4da7e14a00613c518b7dae"), "Incorrect puzzle hash"


async def test_get_coin_records_by_parent_ids():

    node = get_client(NODE_PROVIDER, timeout=None)
    
    height_start = None
    height_end = None
    parent_ids = [hexstr_to_bytes32("0x74acdbfea0d95404526ebc243f7be70b84192ba9237ee0948fc2bc42e5d324a5"),
                  hexstr_to_bytes32("0x453271a545ff4b2b5ff9970f663861791d2ab0e3348c491002b733d50ec9f042"),
                  hexstr_to_bytes32("0x914866872be973b816ff8f341b79b1c05e690b4d414b20e5744ad403cb665f6a")]

    # Test 1
    page = 1

    response = await node.get_coin_records_by_parent_ids(parent_ids, height_start, height_end, True, page)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    if NODE_PROVIDER == NodeProvider.MOJONODE:
        assert len(response) >= 50, "Missing coin records"
        assert len(response) <= 50, "Coin records page exceeds 50 items"
        
    # Test 2
    page = 5
    
    response = await node.get_coin_records_by_parent_ids(parent_ids, height_start, height_end, True, page)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    if NODE_PROVIDER == NodeProvider.MOJONODE:
        assert len(response) >= 1, "Missing coin records"
        assert len(response) <= 1, "Coin records page exceeds 1 item"


async def test_get_coin_records_by_puzzle_hash():

    node = get_client(NODE_PROVIDER)
    
    height_start = None
    height_end = None
    include_spent_coins = False
    page = 1

    # Test 1
    puzzle_hash = hexstr_to_bytes32("0xf9cd704e2aace4203e17ed600bfc9fd20f475671e30d41cae912090febf16c20")

    response = await node.get_coin_records_by_puzzle_hash(puzzle_hash, height_start, height_end, include_spent_coins, page)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert len(response) >= 10, "Missing coin record(s)"
    assert len(response) <= 10, "Unexpected coin record(s) returned"
    coin_records = sorted(response, key=lambda x: x.coin.name())
    response.sort(key=lambda x: x.coin.name())
    assert response[0].coin.parent_coin_info == hexstr_to_bytes32("512c410853414ad5043d08c858ee21bfa3b52a21174daa6774ddaeb2097f6f9b"), "Parent coin info does not match"
    assert response[9].coin.parent_coin_info == hexstr_to_bytes32("55bb15e4acfb0cb9aea993fc8e9461c8fdb865a08995e011896935e7235e95dc"), "Parent coin info does not match"
    
    # Test 2
    puzzle_hash = hexstr_to_bytes32("0x0833a81b2b85b4bdb2f1b2dbca0386636d3485cc5605a80433e3a2c2fdaa0f5a")

    response = await node.get_coin_records_by_puzzle_hash(puzzle_hash, height_start, height_end, include_spent_coins, page)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert len(response) >= 1, "Missing coin record(s)"
    assert len(response) <= 1, "Unexpected coin record(s) returned"
    assert response[0].coin.parent_coin_info == hexstr_to_bytes32("319e7c6d6a30000c5c730d94f00334d09c4bf2c78294de22402aaa4209da74c9"), "Parent coin info does not match"
    assert response[0].confirmed_block_index == 4219519, "Incorrect confirmed block index"
    assert response[0].timestamp == 1694508671, "Incorrect timestamp"

    
async def test_get_coin_records_by_puzzle_hashes():

    node = get_client(NODE_PROVIDER)
    
    height_start = None
    height_end = None
    include_spent_coins = False
    puzzle_hashes = [
        hexstr_to_bytes32("0xf9cd704e2aace4203e17ed600bfc9fd20f475671e30d41cae912090febf16c20"),
        hexstr_to_bytes32("0x0833a81b2b85b4bdb2f1b2dbca0386636d3485cc5605a80433e3a2c2fdaa0f5a")
    ]

    # Test 1
    page = 1    
    response = await node.get_coin_records_by_puzzle_hashes(puzzle_hashes, height_start, height_end, include_spent_coins, page)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert len(response) >= 11, "Missing coin record(s)"
    assert len(response) <= 11, "Unexpected coin record(s) returned"
    response.sort(key=lambda x: x.coin.name())
    assert response[0].coin.parent_coin_info == hexstr_to_bytes32("512c410853414ad5043d08c858ee21bfa3b52a21174daa6774ddaeb2097f6f9b"), "Parent coin info does not match"
    assert response[10].coin.parent_coin_info == hexstr_to_bytes32("55bb15e4acfb0cb9aea993fc8e9461c8fdb865a08995e011896935e7235e95dc"), "Parent coin info does not match"


async def test_get_coin_records_by_hint():

    node = get_client(NODE_PROVIDER, timeout=None)
    
    height_start = None #400000
    height_end = None #1900000
    include_spent_coins = True
    hint = hexstr_to_bytes32("0x6916079cc35f377e96fa34af87d14f58ce1f08d864f93e89bbdd04a26f591540")

    response = await node.get_coin_records_by_hint(hint, height_start, height_end, include_spent_coins, 1)

    assert isinstance(response, list), "Response is not a list (or missing)"
    for cr in response:
        assert isinstance(cr, CoinRecord), "Element in response list is not a coin record (or missing)"
    assert len(response) >= 3, "Missing coin record(s)"
    assert len(response) <= 3, "Unexpected coin record(s) returned"
    coin_records = sorted(response, key=lambda x: x.coin.name())
    assert coin_records[0].timestamp == 1650620445, "Incorrect timestamp"
    assert coin_records[1].timestamp == 1650533680, "Incorrect timestamp"
    assert coin_records[1].coin.puzzle_hash == hexstr_to_bytes32("0xd229b55df95852e99f1c2708a7248380676ead58fd6a3cbfb44c870204506751"), "Incorrect puzzle hash"
    assert coin_records[2].timestamp == 1679530148, "Incorrect timestamp"
    assert coin_records[2].confirmed_block_index == 3416908, "Incorrect confirmed block index"


async def test_get_block_record_by_height():

    node = get_client(NODE_PROVIDER)
    
    # Test 1
    block_height = 4000000

    response = await node.get_block_record_by_height(block_height)

    assert isinstance(response, BlockRecord), "Response is not a block record (or missing)"
    assert response.height == block_height, "Incorrect block height"
    assert response.header_hash == hexstr_to_bytes32("0x12dae76a009f2869bf84db08761aa3ec76ade3aef130a743238cbb999dd79700")
    assert response.reward_claims_incorporated is None, "Incorporated reward claims is not None"

    # Test 2
    block_height = 4000791

    response = await node.get_block_record_by_height(block_height)

    assert isinstance(response, BlockRecord), "Response is not a block record (or missing)"
    assert response.height == block_height, "Incorrect block height"
    assert response.header_hash == hexstr_to_bytes32("0x5fcdbbf6b8ed8b6752861533be08a72cc17d4b2d0b257fa3d9462dc6cab4a383"), "Block header hash does not match"
    assert response.total_iters == 16857075060335, "Number of total iterations does not match"
    assert response.farmer_puzzle_hash == hexstr_to_bytes32("0x883cc9684d9ea89e96b4676be71c14fb67223fc211c135c6fb2332b32ec95dce"), "Farmer puzzle hash does not match"
    assert len(response.reward_claims_incorporated) == 6, "Number of incorporated reward claims does not match"
    


async def test_get_block_record():
    
    node = get_client(NODE_PROVIDER)
    
    # Test 1
    header_hash = GENESIS_BLOCK_HEADER_HASH["mainnet"]

    response = await node.get_block_record(header_hash)

    assert isinstance(response, BlockRecord), "Response is not a block record (or missing)"
    assert response.height == 0, "Incorrect block height"
    assert response.farmer_puzzle_hash == hexstr_to_bytes32("0x3d8765d3a597ec1d99663f6c9816d915b9f68613ac94009884c4addaefcce6af"), "Incorrect farmer puzzle hash"
    assert response.signage_point_index == 2, "Incorrect signage point index"

    # Test 2
    header_hash = hexstr_to_bytes32("0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d")

    response = await node.get_block_record(header_hash)

    assert isinstance(response, BlockRecord), "Response is not a BlockRecord (or missing)"
    assert response.height == 4030597, "Incorrect block height"
    assert response.prev_transaction_block_height == 4030594, "Incorrect previous transaction block height"
    assert response.farmer_puzzle_hash == hexstr_to_bytes32("0x907491ca39c35bc1f9a6eda33f7c0f97a9f583975088dad7216f1edd79f522ae"), "Incorrect farmer puzzle hash"
    assert response.signage_point_index == 22, "Incorrect signage point index"


async def test_get_block_records():

    node = get_client(NODE_PROVIDER)

    # Note: Mojonode get_block_records endpoint returns a list of block records ordered ascending by height
    
    # Test 1
    height_start = 0
    height_end = 100

    response = await node.get_block_records(height_start, height_end)

    assert isinstance(response, list), "Response not a list (or missing)"
    for br in response:
        assert isinstance(br, BlockRecord), "Element in response list is not a block record"
    assert len(response) >= height_end - height_start, "Block record(s) missing"
    assert len(response) <= height_end - height_start, "Too many block records"
    for h in range(height_start, height_end):
        assert response[h].height == h, "Incorrect block height"

    # Test 2
    height_start = 4000000
    height_end = 4000100

    response = await node.get_block_records(height_start, height_end)

    assert isinstance(response, list), "Response not a list (or missing)"
    for br in response:
        assert isinstance(br, BlockRecord), "Element in response list is not a block record"
    assert len(response) >= height_end - height_start, "Block record(s) missing"
    assert len(response) <= height_end - height_start, "Too many block records"
    for h in range(len(response)):
        assert response[h].height == height_start + h, "Incorrect block height"


async def test_get_block():

    node = get_client(NODE_PROVIDER)

    # Test 1
    header_hash = GENESIS_BLOCK_HEADER_HASH["mainnet"]
    
    response = await node.get_block(header_hash)

    assert isinstance(response, FullBlock), "Response not a full block (or missing)"
    assert response.reward_chain_block.infused_challenge_chain_ip_vdf is None, "Infused challenge chain ip vdf is not None"
    assert response.infused_challenge_chain_ip_proof is None, "Infused challenge chain ip proof is not None"
    assert response.foliage.reward_block_hash == hexstr_to_bytes32("0xbdde7b5b2bc6025c07a9f5233d8eae167bea654146b272652262b362524c3e85"), "Foliage reward block hash does not match"
    assert response.reward_chain_block.height == 0, "Incorrect reward chain block height"
    assert response.reward_chain_block.signage_point_index == 2, "Incorrect reward chain signage point index"
    assert response.foliage_transaction_block.timestamp == 1616162474, "Incorrect folisage transaction block timestamp"


    # Test 2
    header_hash = hexstr_to_bytes32("0x7357071bb77de2e98b9b1daf6b87f67dd8481fa144bcc03d331dba8664fc04f9") # BH 1 (transaction block w/o transactions)
    
    response = await node.get_block(header_hash)

    assert isinstance(response, FullBlock), "Response not a full block (or missing)"
    assert response.reward_chain_block.infused_challenge_chain_ip_vdf.output.data == bytes.fromhex("03009234229b9b02119b34afb811537d2410e64c55cf7931d35bc46c5225319c332c80257f57cf732108f9896572196b9bbe10010d9897ce3d8109de6a3a8de2f90617802df029dabdcc42820f885a4ded4b77471a60c6ab8be114147ad29674770a0d02"), "Incorrect reward chain block infused challenge chain ip vdf output data"
    assert response.infused_challenge_chain_ip_proof.witness == bytes.fromhex("0000ff08ba57f4c3a23664c9d2eb74d5c9ab5d6c5d4f2f1114b4cca332d38bba6932d977ad1114a3e43574283cb5aec1b809418c2c5f6677e5440cb5ebb7e64ed51188ab7314749d3cf645fb32472e0f8d6bc882a144a1c858add7b245f305760830010000000000001f7ee4abecfc8d6bdad098e506d290b98679bafa52023c97eb3d801806931045f6f70893010037aeeb3d8de790c5ae9309481e7948fe6738983bdbb5896d11f92e6407d4276e450a5187ba20ff8346a84b055737d11f8d99c54305054b8f2ccb043f4c30891f688e6720c449b7d27b7c6c87b1d2135ee3540b1c5c2c1e0dd9705e4cdcee4f4c010000000000005e7cace34286b8e38e7b74aabade713b08db92326bfb7a98ed0a605ffa3e0a5853f63769030073a11fc71eaa8796da31dd464988081e5b1d3c9bc25829cefa3af42b2639297e2cc6eda1473eda02aad9d688afde353767066e1be6834abb5a3c93849158a4433acb2f32990e4a2f8bf092ad747f3376b76316cc07e2d0fa081054caa9a4262f0100"), "Incorrect infused challenge chain ip proof witness"
    assert response.foliage_transaction_block.transactions_info_hash == hexstr_to_bytes32("0xdd5e642b2e1c2cc40316360dd2b636f6853af4781a03354b2cad04a90ebac7ab"), "Incorrect foliage transaction block transactions info hash"
    assert response.foliage_transaction_block.timestamp == 1616162525, "Incorrect folisage transaction block timestamp"
    assert response.reward_chain_block.height == 1, "Incorrect reward chain block height"
    assert response.reward_chain_block.signage_point_index == 7, "Incorrect reward chain block signage point index"
    
    

    # Test 3
    header_hash = hexstr_to_bytes32("0x9ec0447c9a4f5183f3235523aacf01fefb915f5ad90e2b5f1b45894412a4fb92") # BY 4030596 (not a transaction block)
    
    response = await node.get_block(header_hash)

    assert isinstance(response, FullBlock), "Response is not a full block (or missing)"
    assert response.transactions_info is None, "Transactions info is not None"
    assert response.foliage_transaction_block is None, "Foliage transaction block is not None"
    assert response.infused_challenge_chain_ip_proof.witness == bytes.fromhex("03007f400e17ffe72216d175d2cbfbaeda8ff0e656c94662d88292c58590cc38e8955e3d71e06e3edb4318ed1834190a1872b193f76d07ee80222ae83d3b0dbe5a56d7aa2de5771bce34b381402ccb36b1fa659bda8e3e17b8b5649a4c60ccbc9c590100000000000006cbd8898b4ff9a6711aca9bc59883bc04fd23b884ecf71000273af996aa2a5ccb58bdf7000095e44fa0c00565f14ec19b01544ec0be3f0e528989a04f3d8f1c16840bbf354c7d76834cb4f188a6357a5c4ef9671dfdfb0b15b5dd86682332cf9e3108455c5585881cb57d6d690ecde1720d7bd9935a534409ac60de28d31da3d39ad8a1d24f01000000000000146388b701421a7a9db2ee1371c9096291df3c02a4d5210e8c2b4a895b632f86c6606265000089b88f5e3048cfcd6060897f7f6c7307bd676e2fbfdce41a6b997a870c1611e46b6805f24cbf4721170dc70434ca830d479c9b117824273bc680f587e75ea5629e96e7df77a7ae28081b9cc0f120d2d367c527a5ec5fc0f05dba11c5816132270100"), "Incorrect infused challenge chain ip proof witness"
    assert response.reward_chain_block.height == 4030596, "Incorrect reward chain block height"
    assert response.reward_chain_block.signage_point_index == 19, "Incorrect reward chain block signage point index"
    
    
    # Test 4
    header_hash = hexstr_to_bytes32("0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d") # BH 4030597 (transaction block w/ transactions)
    
    response = await node.get_block(header_hash)

    assert isinstance(response, FullBlock), "Response body is not a full block (or missing)"
    assert response.transactions_info.generator_root == hexstr_to_bytes32("0xeab5b7737872d499f743eff698117e2a97435464ff0356f270a2acb35297ff8f"), "Incorrect transactions info generator root"
    assert len(response.transactions_info.reward_claims_incorporated) == 4, "Incorrect length of transactions info reward claims incorporated"
    assert response.foliage_transaction_block.transactions_info_hash == hexstr_to_bytes32("0xb3e638edbe7336ea5be2cb56338b701051c78135e6588129faaf61d56c93f073"), "Incorrect foliage transaction block transactions info hash"
    assert response.infused_challenge_chain_ip_proof.witness == bytes.fromhex("02006ce32ae3b2a182d8d0f2dece55d33a916bb95931052bf48984394453eda943e365399c7c5ef154bf0940ca8f5aaf40c8c3d0c20e26e68c7ad6f13706257b5f072118dc0ed2ad462baf00de2d564555a1d4ca8f0468b494a877b3278bc1acc2060803000000000014b6bcbdf62e7821ffd993920e728172bed444709de589840b69180aa096a1322337068f030095fb42b26a19044047a7679a45252042bbb170d6eb9286bf6a297bbebff0a0009b35f3f3d0d9efc13ec47b7a5ceeb9d6cdc23a1491e7e3614aa807a5e44a88322de4077f22265dd93a8c428a1baeb9984c3d23cc7cb78d85b6834249f4b9763d010000000000003e23d0d5573a8c5f3c23276cbbb9cdf9f8088428302799b866de43c66d489650d79e90f70100a4f88abf453fad54e0ec884db804f2ab6dc54833d6ad89dc959bf063c77e7f53f0427782fc74904e51ea9dc35ff43e1facbde1b00ce7575b8ff59756f74a0c57abddd8d9263084bdb771fd32358950c526ab5f405885d41850f46e8c40456f7b0100"), "Incorrect infused challenge chain ip proof witness"
    assert response.reward_chain_block.height == 4030597, "Incorrect reward chain block height"
    assert response.reward_chain_block.signage_point_index == 22, "Incorrect reward chain block signage point index"

    
async def test_get_blocks():

    node = get_client(NODE_PROVIDER)

    height_start = 4030570
    height_end = 4030620
    
    response = await node.get_blocks(height_start, height_end)

    assert isinstance(response, list), "Response is not a list (or missing)"
    assert len(response) >= height_end - height_start, "Block(s) missing"
    assert len(response) <= height_end - height_start, "Unexpected block(s)"
    for b in response:
        assert isinstance(b, FullBlock), "Element in response list is not a full block"
    for h in range(height_end - height_start):
        
        # Check whether we are dealing with a transaction block or not
        transaction_block = True
        if response[h].transactions_info is None:
            transaction_block = False
        if transaction_block:
            assert isinstance(response[h].transactions_info.generator_root, bytes32), "Transactions info generator root is not of type bytes32"
            assert isinstance(response[h].foliage_transaction_block.transactions_info_hash, bytes32), "Foliage transaction block transactions info hash is not of type bytes32"
        else:
            assert response[h].transactions_info is None, "Transaction info is not None"
            assert response[h].foliage_transaction_block is None, "Foliage transaction block is not None"


async def test_get_additions_and_removals():

    node = get_client(NODE_PROVIDER)

    # Test 1
    header_hash = hexstr_to_bytes32("0x7357071bb77de2e98b9b1daf6b87f67dd8481fa144bcc03d331dba8664fc04f9") # BH 1 (transaction block w/o transactions)
    
    response = await node.get_additions_and_removals(header_hash)

    assert isinstance(response, tuple), "Response is not a tuple (or missing)"
    assert len(response) == 2, "Response is not a typle of length 2"
    for c in response[0]:
        assert isinstance(c, CoinRecord), "Element in additions list is not a coin record"
    for c in response[1]:
        assert isinstance(c, CoinRecord), "Element in removals list is not a coin record"
    assert len(response[0]) == 2, "Incorrect number of additions"
    assert len(response[1]) == 0, "Incorrect number of removals"
    response[0].sort(key=lambda x: x.coin.name())
    response[1].sort(key=lambda x: x.coin.name())
    assert response[0][0].coin.parent_coin_info == hexstr_to_bytes32("ccd5bb71183532bff220ba46c268991a00000000000000000000000000000000"), "Incorrect parent coin info of addition"
    assert response[0][1].coin.parent_coin_info == hexstr_to_bytes32("3ff07eb358e8255a65c30a2dce0e5fbb00000000000000000000000000000000"), "Incorrect parent coin info of addition"

    # Test 2
    header_hash = hexstr_to_bytes32("0xbb8ba4b1baaefa8a69520116f50ee202d077309f8b31554963f201bb80c4dd30") # BH 1 (transaction block w/o transactions)
    
    response = await node.get_additions_and_removals(header_hash)

    assert isinstance(response, tuple), "Response is not a tuple (or missing)"
    assert len(response) == 2, "Response is not a typle of length 2"
    for c in response[0]:
        assert isinstance(c, CoinRecord), "Element in additions list is not a coin record"
    for c in response[1]:
        assert isinstance(c, CoinRecord), "Element in removals list is not a coin record"
    assert len(response[0]) == 312, "Incorrect number of additions"
    assert len(response[1]) == 58, "Incorrect number of removals"
    response[0].sort(key=lambda x: x.coin.name())
    response[1].sort(key=lambda x: x.coin.name())
    assert response[0][0].coin.parent_coin_info == hexstr_to_bytes32("e98cca3c3ef5aba71d169fc52cbf1d5aedfcbc5c29a76487d609bce3392df934"), "Incorrect parent coin info of addition"
    assert response[0][0].coin.puzzle_hash == hexstr_to_bytes32("b2c984715b8270e9fc0184929b90a1a39edcae47062d7fb408d3b789abbcb206"), "Incorrect puzzle hash of addition"
    assert response[0][0].coin.amount == 35423417832, "Incorrect amount of addition"
    assert response[0][-1].coin.parent_coin_info == hexstr_to_bytes32("e98cca3c3ef5aba71d169fc52cbf1d5aedfcbc5c29a76487d609bce3392df934"), "Incorrect parent coin info of addition"
    assert response[0][-1].coin.puzzle_hash == hexstr_to_bytes32("36acf00e8a895cea36e26306ed4e34d7bb7824fb30e462cad67b29b2d3359e7d"), "Incorrect puzzle hash of addition"
    assert response[1][0].coin.parent_coin_info == hexstr_to_bytes32("ccd5bb71183532bff220ba46c268991a000000000000000000000000004368db"), "Incorrect parent coin info of addition"
    assert response[1][-1].coin.parent_coin_info == hexstr_to_bytes32("e2987bf4f93b30d5f7c9edd6fa7ceccc95707a77ecdf683fbe5934c5de5e5422"), "Incorrect parent coin info of addition"

        
async def test_get_blockchain_state(blockchain_state_keys, peak_keys, sync_keys):

    node = get_client(NODE_PROVIDER)

    response = await node.get_blockchain_state()

    assert isinstance(response, dict), "Response is not a dict (or missing)"
    if response["peak"] is not None:
        assert isinstance(response["peak"], BlockRecord), "Blockchain peak is not a block record"
    assert set(sync_keys).issubset(response["sync"].keys()), "Missing key(s) in sync"


async def test_get_puzzle_and_solution():

    node = get_client(NODE_PROVIDER)

    coin_id = hexstr_to_bytes32("0x9e3a9d74afb7023d4f2828cb9c526052ac007f857d5bdb61b24f3356241056b8")
    height_spent = 4026436

    # Sufficient to pass coin_id only with Mojonode. Official Chia RPC requires height_spent parameter in addition
    response = await node.get_puzzle_and_solution(coin_id, height_spent) #4032845

    assert isinstance(response, CoinSpend), "Response body not a coin spend (or missing)"
    assert response.coin.parent_coin_info == hexstr_to_bytes32("0x8424de665637aff43f54f7e45c145f0d92392825792b3bfe31a721204386fb91"), "Incorrect parent coin info"
    assert response.puzzle_reveal == SerializedProgram.fromhex("0xff02ffff01ff02ffff01ff02ffff03ff0bffff01ff02ffff03ffff09ff05ffff1dff0bffff1effff0bff0bffff02ff06ffff04ff02ffff04ff17ff8080808080808080ffff01ff02ff17ff2f80ffff01ff088080ff0180ffff01ff04ffff04ff04ffff04ff05ffff04ffff02ff06ffff04ff02ffff04ff17ff80808080ff80808080ffff02ff17ff2f808080ff0180ffff04ffff01ff32ff02ffff03ffff07ff0580ffff01ff0bffff0102ffff02ff06ffff04ff02ffff04ff09ff80808080ffff02ff06ffff04ff02ffff04ff0dff8080808080ffff01ff0bffff0101ff058080ff0180ff018080ffff04ffff01b085a35d9fa7068c004e3a6173cff6f6cb4c9e1d6e03de0ef43096a2170d0d6ae0382f83a833d61797964c20bb38d3bb2aff018080"), "Incorrect puzzle reveal"
    assert response.solution == SerializedProgram.fromhex("0xff80ffff01ffff33ffa00833a81b2b85b4bdb2f1b2dbca0386636d3485cc5605a80433e3a2c2fdaa0f5aff0180ffff33ffa0fa48420eba0456dd5128e359cf57ee7a9d10556d84aaf4ef05f245c78717ee3dff8600e8d449827f80ffff34ff835b8d8080ffff3cffa02db46db081105e8ba47e43abf570668090057f42f302a3ff3f25a11ab012fd9c8080ff8080"), "Incorrect solution"

    
async def test_get_block_spends(spend_keys):

    node = get_client(NODE_PROVIDER)

    header_hash = hexstr_to_bytes32("0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d")
    
    response = await node.get_block_spends(header_hash)

    assert isinstance(response, list), "Response not a list (or missing)"
    for s in response:
        assert isinstance(s, CoinSpend), "Element in list is not a coin spend"
    assert len(response) >= 8, "Missing block spend(s)"
    assert len(response) <= 8, "Unexpected block spend(s)"
        

async def test_get_all_mempool_tx_ids():

    node = get_client(NODE_PROVIDER)

    response = await node.get_all_mempool_tx_ids()

    for tid in response:
        assert isinstance(tid, bytes32), "Mempool transaction ID is not of type bytes32"


async def test_get_mempool_item_by_tx_id(converted_mempool_item_required_keys):

    node = get_client(NODE_PROVIDER)

    # First, pick an item from the mempool
    tx_id = ""
    while tx_id == "":
        response = await node.get_all_mempool_tx_ids()
        if response:
            tx_id = response[0]
        else:
            asyncio.sleep(3)

    # Once we've picked a mempool item, get the details
    response = await node.get_mempool_item_by_tx_id(tx_id)

    assert isinstance(response, dict), "Response is not a dict (or missing)"
    assert set(converted_mempool_item_required_keys).issubset(set(response.keys())), "Missing key(s) in mempool item"

    
async def test_get_initial_freeze_period():

    node = get_client(NODE_PROVIDER)

    response = await node.get_initial_freeze_period()

    assert isinstance(response, int), "Response is not a dict (or missing)"
    assert response == 1620061200, "INITIAL_FREE_END_TIMESTAMP does not match"


async def test_healthz():

    node = get_client(NODE_PROVIDER)

    response = await node.healthz()

    assert isinstance(response, bool), "Response is not a boolean (or missing)"
    assert response == True, "Not healthy"


async def test_get_routes():

    node = get_client(NODE_PROVIDER)

    response = await node.get_routes()

    assert isinstance(response, list), "Response is not a list (or missing)"
    if NODE_PROVIDER == NodeProvider.FULLNODE:
        assert len(response) >= 28, "Missing routes"
        assert len(response) <= 28, "Unknown route returned"
    elif NODE_PROVIDER == NodeProvider.MOJONODE:
        assert len(response) >= 27, "Missing routes"
        assert len(response) <= 27, "Unknown route returned"
        

