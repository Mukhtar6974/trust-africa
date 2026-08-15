"""Read-only gateway to the deployed Trust Africa intelligent contract.

State-changing calls intentionally do not live here: browser users submit those
with their own GenLayer-compatible wallets. The Flask API only exposes finalized
contract views through the official GenLayer CLI.
"""

import json
import os
import subprocess


class GenLayerConfigurationError(RuntimeError):
    pass


class GenLayerReadError(RuntimeError):
    pass


class GenLayerGateway:
    def __init__(self, contract_address=None, rpc_url=None, runner=None):
        self.contract_address = contract_address or os.getenv("TRUST_AFRICA_CONTRACT_ADDRESS", "")
        self.rpc_url = rpc_url or os.getenv("TRUST_AFRICA_RPC_URL", "")
        self._runner = runner or subprocess.run

    def _require_configuration(self):
        if not self.contract_address:
            raise GenLayerConfigurationError("TRUST_AFRICA_CONTRACT_ADDRESS is required")
        if not self.rpc_url:
            raise GenLayerConfigurationError("TRUST_AFRICA_RPC_URL is required")

    def read(self, method, *args):
        self._require_configuration()
        command = [
            "genlayer", "call", self.contract_address, method,
            "--rpc", self.rpc_url,
        ]
        if args:
            command.extend(["--args", *(str(arg) for arg in args)])
        completed = self._runner(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise GenLayerReadError(message or "GenLayer read failed")
        output = completed.stdout.strip()
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output


gateway = GenLayerGateway()
