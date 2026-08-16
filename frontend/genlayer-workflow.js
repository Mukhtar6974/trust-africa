export function createGenLayerClients(createClient, chain, account, provider) {
    return {
        readClient: createClient({ chain }),
        writeClient: createClient({ chain, account, provider })
    };
}

export function requireSuccessfulExecution(receipt, executionResult) {
    const outcome = receipt?.txExecutionResultName;
    if (outcome !== executionResult.FINISHED_WITH_RETURN) {
        const detail = receipt?.stderr || receipt?.result?.stderr || outcome || "unknown";
        throw new Error(`GenLayer transaction execution failed: ${detail}`);
    }
    return receipt;
}

export async function writeAndFinalizeTransaction(
    writeClient,
    readClient,
    transaction,
    transactionStatus,
    executionResult
) {
    const hash = await writeClient.writeContract(transaction);
    const receipt = await readClient.waitForTransactionReceipt({
        hash,
        status: transactionStatus.FINALIZED
    });
    requireSuccessfulExecution(receipt, executionResult);
    return hash;
}
