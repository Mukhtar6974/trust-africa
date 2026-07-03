"""Windows compatibility helpers for official genlayer-test direct mode.

The official GenLayer test loader downloads and extracts the GenVM runtime into
``~/.cache/gltest-direct``. On Windows, genlayer-test 0.29.2 attempts to unlink
the temporary stdin file immediately after ``os.dup2(fd, 0)``. POSIX permits
unlinking an open file; Windows does not. This patch keeps the official loader
path intact and defers deletion until the VM restores stdin during cleanup.
"""

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def windows_stdin_tempfile_cleanup(monkeypatch):
    if os.name != "nt":
        return

    import gltest.direct.loader as loader
    import gltest.direct.vm as vm_module

    def _inject_message_to_fd0_windows(vm):
        try:
            from genlayer.py import calldata
            from genlayer.py.types import Address
        except ImportError:
            return

        sender_addr = vm.sender
        if isinstance(sender_addr, bytes):
            sender_addr = Address(sender_addr)

        contract_addr = vm._contract_address
        if isinstance(contract_addr, bytes):
            contract_addr = Address(contract_addr)

        origin_addr = vm.origin
        if isinstance(origin_addr, bytes):
            origin_addr = Address(origin_addr)

        message_data = {
            "contract_address": contract_addr,
            "sender_address": sender_addr,
            "origin_address": origin_addr,
            "stack": [],
            "value": vm._value,
            "datetime": vm._datetime,
            "is_init": False,
            "chain_id": vm._chain_id,
            "entry_kind": 0,
            "entry_data": b"",
            "entry_stage_data": None,
        }

        encoded = calldata.encode(message_data)
        fd, path = tempfile.mkstemp()
        try:
            os.write(fd, encoded)
            os.lseek(fd, 0, os.SEEK_SET)
            vm._original_stdin_fd = os.dup(0)
            vm._genlayer_temp_stdin_path = path
            os.dup2(fd, 0)
        finally:
            os.close(fd)

    original_cleanup = vm_module.VMContext._cleanup_after_deactivate

    def _cleanup_after_deactivate_windows(self):
        temp_path = getattr(self, "_genlayer_temp_stdin_path", None)
        try:
            original_cleanup(self)
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass
                self._genlayer_temp_stdin_path = None

    monkeypatch.setattr(loader, "_inject_message_to_fd0", _inject_message_to_fd0_windows)
    monkeypatch.setattr(
        vm_module.VMContext,
        "_cleanup_after_deactivate",
        _cleanup_after_deactivate_windows,
    )


@pytest.fixture(autouse=True)
def direct_mode_llm_mocks(direct_vm):
    """Mock non-deterministic AI calls for repeatable direct GenVM tests."""
    direct_vm.mock_llm(
        "trade verification expert",
        '{"decision":"APPROVED","confidence":94,"risk":"LOW","reason":"Mocked direct-mode trade evidence approval"}',
    )
    direct_vm.mock_llm(
        "dispute resolution expert",
        '{"decision":"RELEASE_FUNDS","reason":"Mocked direct-mode dispute evidence supports seller"}',
    )
    direct_vm.mock_llm(
        "business trust verification expert",
        '{"status":"VERIFIED","reason":"Mocked direct-mode passport verification"}',
    )
