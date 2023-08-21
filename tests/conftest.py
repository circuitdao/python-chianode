import pytest

GENESIS_BLOCK_HEADER_HASH = {
    "mainnet": "0xd780d22c7a87c9e01d98b49a0910f6701c3b95015741316b3fda042e5d7b81d2"
}

#header_hash = "0x7357071bb77de2e98b9b1daf6b87f67dd8481fa144bcc03d331dba8664fc04f9" # BH 1 (transaction block w/o transactions)
#header_hash = "0x058740efbd4bc33e23c46ff8b9f3207879e10aa96fe0d62ea976320f268b6f27" # BH 250005 (transaction block w/ transactions) -> additions and removals
#header_hash = "0x9ec0447c9a4f5183f3235523aacf01fefb915f5ad90e2b5f1b45894412a4fb92" # BH 4030596 (not a transaction block)
#header_hash = "0xc00bb14a70691fe4bcbfcd1682a0d4d5519bb5c019348e1b8b468a126a9b3e6d" # BH 4030597 (transaction block w/ transactions)


@pytest.fixture
def coin_record_keys():
    return ['coin', 'confirmed_block_index', 'spent_block_index', 'coinbase', 'timestamp', 'spent']

@pytest.fixture
def foliage_keys():
    return ['prev_block_hash', 'reward_block_hash', 'foliage_block_data', 'foliage_block_data_signature',
            'foliage_transaction_block_hash', 'foliage_transaction_block_signature']

@pytest.fixture
def foliage_block_data_keys():
    return ['pool_target', 'extension_data', 'pool_signature', 'farmer_reward_puzzle_hash', 'unfinished_reward_block_hash']

@pytest.fixture
def transactions_info_keys():
    return ['cost', 'fees', 'generator_root', 'generator_refs_root', 'aggregated_signature', 'reward_claims_incorporated']

@pytest.fixture
def foliage_transaction_block_keys():
    return ['timestamp', 'filter_hash', 'removals_root', 'additions_root', 'transactions_info_hash', 'prev_transaction_block_hash']

@pytest.fixture
def vdf_keys():
    return ['output', 'challenge', 'number_of_iterations']

@pytest.fixture
def proof_keys():
    return ['witness', 'witness_type', 'normalized_to_identity']

@pytest.fixture
def proof_of_space_keys():
    return ['size', 'proof', 'challenge', 'plot_public_key', 'pool_public_key', 'pool_contract_puzzle_hash']

@pytest.fixture
def reward_chain_block_keys():
    return ['height', 'weight', 'total_iters', 'proof_of_space', 'reward_chain_ip_vdf', 'reward_chain_sp_vdf',
            'signage_point_index', 'is_transaction_block', 'challenge_chain_ip_vdf', 'challenge_chain_sp_vdf',
            'pos_ss_cc_challenge_hash', 'reward_chain_sp_signature', 'challenge_chain_sp_signature',
            'infused_challenge_chain_ip_vdf']

@pytest.fixture
def block_keys():
    return ['foliage', 'transactions_info', 'finished_sub_slots', 'reward_chain_block', 'reward_chain_ip_proof',
            'reward_chain_sp_proof', 'transactions_generator', 'challenge_chain_ip_proof', 'challenge_chain_sp_proof',
            'foliage_transaction_block', 'transactions_generator_ref_list', 'infused_challenge_chain_ip_proof']

@pytest.fixture
def block_record_keys():
    return ['fees', 'height', 'weight', 'deficit', 'overflow', 'prev_hash', 'timestamp', 'header_hash',
            'total_iters', 'required_iters', 'sub_slot_iters', 'pool_puzzle_hash', 'farmer_puzzle_hash', 
            'signage_point_index', 'challenge_vdf_output', 'challenge_block_info_hash', 'reward_claims_incorporated',
            'sub_epoch_summary_included', 'finished_reward_slot_hashes', 'prev_transaction_block_hash',
            'infused_challenge_vdf_output', 'prev_transaction_block_height', 'reward_infusion_new_challenge',
            'finished_challenge_slot_hashes', 'finished_infused_challenge_slot_hashes']

@pytest.fixture
def additions_removals_keys():
    return ['additions', 'removals']

@pytest.fixture
def blockchain_state_keys():
    return ['peak', 'genesis_challenge_initialized', 'sync', 'difficulty', 'sub_slot_iters', 'space', 'mempool_size',
            'mempool_cost', 'mempool_min_fees', 'mempool_max_total_cost', 'block_max_cost', 'node_id']

@pytest.fixture
def peak_keys():
    return ['fees', 'height', 'weight', 'deficit', 'overflow', 'prev_hash', 'timestamp', 'header_hash', 'total_iters',
            'required_iters', 'sub_slot_iters', 'pool_puzzle_hash', 'farmer_puzzle_hash', 'signage_point_index',
            'challenge_vdf_output', 'challenge_block_info_hash', 'reward_claims_incorporated',
            'sub_epoch_summary_included', 'finished_reward_slot_hashes', 'prev_transaction_block_hash',
            'infused_challenge_vdf_output', 'prev_transaction_block_height', 'reward_infusion_new_challenge',
            'finished_challenge_slot_hashes', 'finished_infused_challenge_slot_hashes']

@pytest.fixture
def sync_keys():
    return ['sync_mode', 'synced', 'sync_tip_height', 'sync_progress_height']

@pytest.fixture
def spend_keys():
    return ['coin', 'puzzle_reveal', 'solution']

@pytest.fixture
def transaction_keys():
    return ['fee', 'cost', 'last_state', 'additions', 'removals', 'mempool_item', 'state_updates']

@pytest.fixture
def mempool_item_keys():
    return ['fee', 'cost', 'additions', 'npc_result', 'spend_bundle', 'spend_bundle_name', 'height_added_to_mempool']

@pytest.fixture
def npc_result_keys():
    return ['cost', 'conds', 'error']

@pytest.fixture
def conds_keys():
    return ['cost', 'spends', 'reserve_fee', 'agg_sig_unsafe', 'height_absolute', 'seconds_absolute']

@pytest.fixture
def uncurried_coin_spend_keys():
    return ['puzzle', 'solution']

@pytest.fixture
def spend_bundle_keys():
    return ['coin_spends', 'aggregated_signature']

@pytest.fixture
def latest_singleton_spend_keys():
    return ['latest_spend', 'current_coin']

@pytest.fixture
def latest_spend_keys():
    return ['coin', 'puzzle_reveal', 'solution']

@pytest.fixture
def current_coin_keys():
    return ['coin', 'confirmed_block_index', 'spent_block_index', 'coinbase', 'timestamp', 'spent']

@pytest.fixture
def coin_transactions_keys():
    return ['added_by', 'removed_by']

@pytest.fixture
def query_schema_keys():
    return ['columns', 'name', 'description']

@pytest.fixture
def table_names():
    return ['coin_records', 'block_records', 'coin_spends', 'transactions']

@pytest.fixture
def query_keys():
    return ['success', 'status', 'query_id', 'data', 'columns', 'errors']

@pytest.fixture
def coin_records_columns():
    return ['name', 'puzzle_hash', 'amount', 'confirmed_block_height', 'coinbase', 'parent_coin_name',
            'created_at', 'spent_at', 'puzzle', 'cost', 'solution', 'conditions', 'spent_block_height',
            'memos', 'confirmed_block_name', 'is_spent', 'spent_block_name']

@pytest.fixture
def block_records_columns():
    return ['hash', 'aggregated_signature', 'fees', 'cost', 'weight', 'created_at', 'data', 'prev_hash',
            'height', 'reverted']

@pytest.fixture
def coin_spends_columns():
    return ['conditions', 'cost', 'name', 'puzzle', 'solution', 'spent_at', 'spent_block_height', 'spent_block_name']

@pytest.fixture
def transactions_columns():
    return ['name', 'aggregated_signature', 'fee', 'cost', 'fee_per_cost', 'created_at', 'mempool_item',
            'last_state', 'added_at_height', 'state_updates', 'additions', 'removals']
