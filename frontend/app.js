import { createClient } from "genlayer-js";
import {
    localnet,
    studionet,
    testnetAsimov,
    testnetBradbury,
} from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

const networkName = import.meta.env.VITE_GENLAYER_NETWORK || "testnetBradbury";
const contractAddress = import.meta.env.VITE_GENLAYER_CONTRACT_ADDRESS || "";
const chains = { localnet, studionet, testnetAsimov, testnetBradbury };
const chain = chains[networkName];

let walletAddress = "";
let readClient = chain ? createClient({ chain }) : null;
let writeClient = null;
let currentTradeId = "";

const $ = (id) => document.getElementById(id);

function setText(id, value) {
    $(id).textContent = value == null || value === "" ? "—" : String(value);
}

function setMessage(id, message, isError = false) {
    const element = $(id);
    element.textContent = message;
    element.classList.toggle("error", isError);
}

function jsonReplacer(_key, value) {
    return typeof value === "bigint" ? value.toString() : value;
}

function showConfiguration() {
    setText("networkValue", networkName);
    setText("contractAddress", contractAddress || "Not configured");
    if (!chain) {
        setMessage("tradeMessage", `Unsupported GenLayer network: ${networkName}`, true);
    }
    if (!contractAddress) {
        setMessage("tradeMessage", "Set VITE_GENLAYER_CONTRACT_ADDRESS before using the contract.", true);
    }
}

function ensureContractConfiguration() {
    if (!chain) throw new Error(`Unsupported GenLayer network: ${networkName}`);
    if (!contractAddress) throw new Error("The deployed contract address is not configured.");
}

function ensureWallet() {
    ensureContractConfiguration();
    if (!walletAddress || !writeClient) throw new Error("Connect a wallet first.");
}

function showTransaction(operation, hash, receipt) {
    setText("txOperation", operation);
    setText("txHash", hash);
    setText("txFinality", receipt.status || "FINALIZED");
    setText("txExecutionResult", receipt.txExecutionResultName || "Unknown");
}

async function waitForFinalized(hash, operation) {
    const receipt = await readClient.waitForTransactionReceipt({
        hash,
        status: TransactionStatus.FINALIZED,
        fullTransaction: false,
    });
    showTransaction(operation, hash, receipt);
    if (receipt.txExecutionResultName !== ExecutionResult.FINISHED_WITH_RETURN) {
        throw new Error(
            `${operation} finalized with execution result ${receipt.txExecutionResultName || "UNKNOWN"}.`
        );
    }
    return receipt;
}

async function writeContract(functionName, args, operation) {
    ensureWallet();
    const hash = await writeClient.writeContract({
        address: contractAddress,
        functionName,
        args,
        value: BigInt(0),
    });
    return waitForFinalized(hash, operation);
}

async function readFullState(tradeId) {
    ensureContractConfiguration();
    if (!readClient) throw new Error("The GenLayer read client is not available.");

    const trade = await readClient.readContract({
        address: contractAddress,
        functionName: "get_trade",
        args: [tradeId],
    });
    const [buyerPassport, sellerPassport, report] = await Promise.all([
        readClient.readContract({
            address: contractAddress,
            functionName: "get_trust_passport",
            args: [trade.buyer],
        }),
        readClient.readContract({
            address: contractAddress,
            functionName: "get_trust_passport",
            args: [trade.seller],
        }),
        readClient.readContract({
            address: contractAddress,
            functionName: "get_full_trust_report",
            args: [tradeId],
        }),
    ]);

    const state = { trade, buyerPassport, sellerPassport, report };
    $("stateOutput").textContent = JSON.stringify(state, jsonReplacer, 2);
    currentTradeId = tradeId;
    $("disputeTradeId").value = tradeId;
    return state;
}

function syncBuyerAddress() {
    $("buyerAddress").value = walletAddress;
}

async function connectWallet() {
    try {
        ensureContractConfiguration();
        if (!window.ethereum) throw new Error("No browser wallet was found.");
        const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
        walletAddress = accounts[0] || "";
        if (!walletAddress) throw new Error("The wallet returned no account.");
        writeClient = createClient({
            chain,
            account: walletAddress,
            provider: window.ethereum,
        });
        if (typeof writeClient.connect === "function") await writeClient.connect(networkName);
        setText("walletAddress", walletAddress);
        setText("walletStatus", `Connected on ${networkName}`);
        $("walletButton").textContent = "Wallet connected";
        syncBuyerAddress();
        setMessage("tradeMessage", "Wallet connected. Create a trade when ready.");
    } catch (error) {
        setMessage("tradeMessage", error.message, true);
    }
}

async function submitTrade(event) {
    event.preventDefault();
    const button = $("tradeSubmit");
    button.disabled = true;
    try {
        ensureWallet();
        const form = new FormData(event.currentTarget);
        const tradeId = form.get("trade_id");
        const buyer = form.get("buyer");
        const seller = form.get("seller");
        const buyerAddress = walletAddress;
        const sellerAddress = form.get("seller_address");
        const product = form.get("product");
        const amount = BigInt(form.get("amount"));
        const evidence = form.get("evidence");

        setMessage("tradeMessage", "Submitting create_trade and waiting for FINALIZED...");
        await writeContract(
            "create_trade",
            [tradeId, buyer, seller, buyerAddress, sellerAddress, product, amount, evidence],
            "create_trade"
        );

        setMessage("tradeMessage", "Trade created. Submitting validate_trade and waiting for FINALIZED...");
        await writeContract("validate_trade", [tradeId, evidence], "validate_trade");
        await readFullState(tradeId);
        setMessage("tradeMessage", `Trade ${tradeId} finalized and state loaded from GenLayer.`);
        $("readTradeId").value = tradeId;
    } catch (error) {
        setMessage("tradeMessage", error.message, true);
    } finally {
        button.disabled = false;
    }
}

async function submitDispute(event) {
    event.preventDefault();
    const button = $("disputeSubmit");
    button.disabled = true;
    try {
        ensureWallet();
        const form = new FormData(event.currentTarget);
        const tradeId = form.get("trade_id") || currentTradeId;
        setMessage("disputeMessage", "Submitting resolve_dispute and waiting for FINALIZED...");
        await writeContract(
            "resolve_dispute",
            [
                tradeId,
                form.get("buyer_claim"),
                form.get("seller_response"),
                form.get("evidence"),
            ],
            "resolve_dispute"
        );
        await readFullState(tradeId);
        setMessage("disputeMessage", `Dispute for ${tradeId} finalized and state loaded from GenLayer.`);
    } catch (error) {
        setMessage("disputeMessage", error.message, true);
    } finally {
        button.disabled = false;
    }
}

async function submitRead(event) {
    event.preventDefault();
    try {
        const tradeId = $("readTradeId").value.trim();
        if (!tradeId) throw new Error("Enter a trade ID.");
        await readFullState(tradeId);
    } catch (error) {
        $("stateOutput").textContent = error.message;
    }
}

$("walletButton").addEventListener("click", connectWallet);
$("tradeForm").addEventListener("submit", submitTrade);
$("disputeForm").addEventListener("submit", submitDispute);
$("readForm").addEventListener("submit", submitRead);
$("tradeId").value = `TRADE-${Date.now()}`;
showConfiguration();
