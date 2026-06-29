"""
Conftest for direct-mode GenLayer contract tests.

Direct tests deploy and execute the intelligent contract via the GenVM binary.
The binary is downloaded automatically by genlayer-test on first run; this
requires internet access and a compatible gltest version.

If the binary cannot be obtained, all direct tests are skipped rather than
failing with an unhelpful HTTP error.
"""

import pytest


def _genvm_reachable() -> bool:
    """Return True if the GenVM artifact URL resolves (HEAD check, 5 s timeout)."""
    try:
        import urllib.request
        from gltest.direct.sdk_loader import get_version  # type: ignore[import]

        version = get_version()
        url = (
            f"https://github.com/genlayerlabs/genvm/releases/download/"
            f"{version}/genvm-universal.tar.xz"
        )
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


# Evaluate once per session; avoids repeated HEAD requests.
_GENVM_OK: bool | None = None


@pytest.fixture(scope="session", autouse=True)
def require_genvm_binary() -> None:
    """Skip every direct test in this session if the GenVM binary is unavailable."""
    global _GENVM_OK
    if _GENVM_OK is None:
        _GENVM_OK = _genvm_reachable()
    if not _GENVM_OK:
        pytest.skip(
            "GenVM binary unavailable — the required release artifact could not be "
            "fetched from GitHub. Direct tests need internet access and a gltest "
            "version whose expected release tag exists. Unit tests in "
            "tests/test_trust_engine.py run without this dependency."
        )
