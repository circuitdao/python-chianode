from pytest import fixture
from chianode import MojoClient
import httpx


### Test push_tx endpoint ###
async def test_push_tx():

    mojonode = MojoClient()

    # Add spendbundle to broadcast before running test
    tx = ""

    response = await mojonode.push_tx(tx)

    assert response.status_code == httpx.codes.OK, "Response status not OK"
    response_json = response.json()
    assert isinstance(response_json, dict), "Response body not a dict (or missing)"

