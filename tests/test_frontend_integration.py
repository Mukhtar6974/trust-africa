import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
FRONTEND = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
WORKFLOW_URI = (ROOT / "frontend" / "genlayer-workflow.js").as_uri()


def run_node(script):
    completed = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_write_client_uses_browser_wallet_provider_and_read_client_does_not():
    result = run_node(f"""
        import {{ createGenLayerClients }} from {json.dumps(WORKFLOW_URI)};
        const calls = [];
        const provider = {{ request() {{}} }};
        createGenLayerClients(options => {{ calls.push(options); return options; }}, "chain", "0xabc", provider);
        console.log(JSON.stringify({{
            readHasProvider: Object.hasOwn(calls[0], "provider"),
            writeProviderMatches: calls[1].provider === provider,
            writeAccount: calls[1].account
        }}));
    """)
    assert result == {
        "readHasProvider": False,
        "writeProviderMatches": True,
        "writeAccount": "0xabc",
    }


def test_finalized_but_failed_transaction_rejects_ui_workflow():
    result = run_node(f"""
        import {{ writeAndFinalizeTransaction }} from {json.dumps(WORKFLOW_URI)};
        let nextTransactionSent = false;
        const writeClient = {{ writeContract: async () => "0xfailed" }};
        const readClient = {{ waitForTransactionReceipt: async () => ({{
            statusName: "FINALIZED",
            txExecutionResultName: "FINISHED_WITH_ERROR",
            stderr: "UserError"
        }}) }};
        try {{
            await writeAndFinalizeTransaction(
                writeClient,
                readClient,
                {{}},
                {{ FINALIZED: "FINALIZED" }},
                {{ FINISHED_WITH_RETURN: "FINISHED_WITH_RETURN" }}
            );
            nextTransactionSent = true;
            console.log(JSON.stringify({{ rejected: false, nextTransactionSent }}));
        }} catch (error) {{
            console.log(JSON.stringify({{ rejected: true, nextTransactionSent, message: error.message }}));
        }}
    """)
    assert result["rejected"] is True
    assert result["nextTransactionSent"] is False
    assert "UserError" in result["message"]


def test_browser_uses_real_contract_methods_not_flask_writes():
    assert 'writeAndFinalize("create_trade"' in FRONTEND
    assert 'writeAndFinalize("validate_trade"' in FRONTEND
    assert 'writeAndFinalize("resolve_dispute"' in FRONTEND
    assert 'writeAndFinalize("issue_trust_passport"' in FRONTEND
    assert 'readContract("get_full_trust_report"' in FRONTEND
    assert 'fetch("http://127.0.0.1:5000/ai-judge"' not in FRONTEND
    assert 'fetch("http://127.0.0.1:5000/resolve-dispute"' not in FRONTEND
