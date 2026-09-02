import smi_gateway


def test_home_node_token_header_is_allowed_through_private_proxy():
    assert "x-oap-home-node-token" in smi_gateway._ALLOWED_REQUEST_HEADERS
