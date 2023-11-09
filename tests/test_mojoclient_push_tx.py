from pytest import fixture
from tests.conftest import NODE_PROVIDER, get_client

from chia.types.spend_bundle import SpendBundle


### Test push_tx endpoint ###
async def test_push_tx():

    node = get_client(NODE_PROVIDER)

    # This test fails by default. To make it pass, insert a valid spend bundle to be broadcast
    spend_bundle = SpendBundle()

    response = await node.push_tx(spend_bundle)

    assert isinstance(response, dict), "Response body not a dict (or missing)"
