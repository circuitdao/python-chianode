from pytest import fixture
from chianode import MojoClient
import httpx


### Test push_tx endpoint ###
async def test_push_tx():

    mojonode = MojoClient()

    # This test fails by default. To make it pass, insert a spend bundle to be broadcast
    spend_bundle = ""

    response = await mojonode.push_tx(spend_bundle)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"

