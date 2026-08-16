from genlayer_py.types import TransactionHashVariant

from backend.genlayer_gateway import GenLayerGateway


class RecordingClient:
    def __init__(self):
        self.calls = []

    def read_contract(self, **kwargs):
        self.calls.append(kwargs)
        return {"trade_id": kwargs["args"][0]}


def test_view_arguments_use_genlayer_py_and_finalized_state():
    client = RecordingClient()
    gateway = GenLayerGateway(
        contract_address="0x1111111111111111111111111111111111111111",
        network="studionet",
        client=client,
    )

    result = gateway.read("get_full_trust_report", "T-200")

    assert result == {"trade_id": "T-200"}
    assert client.calls == [{
        "address": "0x1111111111111111111111111111111111111111",
        "function_name": "get_full_trust_report",
        "args": ["T-200"],
        "transaction_hash_variant": TransactionHashVariant.LATEST_FINAL,
    }]
