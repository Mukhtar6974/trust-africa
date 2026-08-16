"""Read-only gateway to finalized Trust Africa intelligent-contract state."""

import os


class GenLayerConfigurationError(RuntimeError):
    pass


class GenLayerReadError(RuntimeError):
    pass


def _create_sdk_client(network, rpc_url):
    try:
        from genlayer_py import create_client
        from genlayer_py import chains
    except ImportError as error:
        raise GenLayerConfigurationError(
            "genlayer-py is required for backend contract reads"
        ) from error

    chain_name = network.replace("-", "_")
    chain = getattr(chains, chain_name, None)
    if chain is None:
        raise GenLayerConfigurationError(f"Unsupported GenLayer network: {network}")
    return create_client(chain=chain, endpoint=rpc_url or None)


class GenLayerGateway:
    def __init__(self, contract_address=None, rpc_url=None, network=None, client=None):
        self.contract_address = contract_address or os.getenv("TRUST_AFRICA_CONTRACT_ADDRESS", "")
        self.rpc_url = rpc_url if rpc_url is not None else os.getenv("TRUST_AFRICA_RPC_URL", "")
        self.network = network or os.getenv("TRUST_AFRICA_NETWORK", "studionet")
        self._client = client

    def _require_configuration(self):
        if not self.contract_address:
            raise GenLayerConfigurationError("TRUST_AFRICA_CONTRACT_ADDRESS is required")

    def _get_client(self):
        if self._client is None:
            self._client = _create_sdk_client(self.network, self.rpc_url)
        return self._client

    def read(self, method, *args):
        self._require_configuration()
        try:
            from genlayer_py.types import TransactionHashVariant

            return self._get_client().read_contract(
                address=self.contract_address,
                function_name=method,
                args=list(args),
                transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
            )
        except GenLayerConfigurationError:
            raise
        except Exception as error:
            raise GenLayerReadError(str(error) or "GenLayer read failed") from error


gateway = GenLayerGateway()
