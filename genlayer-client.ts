import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains'; // swap for the Bradbury testnet chain config

// Fill in after deployment (see README).
const CONTRACT_ADDRESS = '0xYOUR_DEPLOYED_FACTANCHOR_ADDRESS';

const client = createClient({
  chain: studionet,
});

/**
 * Submit a new plain-English claim to be resolved by validator consensus.
 * `sourceUrl` is the page every validator will independently fetch —
 * required so the claim is verifiable consistently across nodes.
 */
export async function submitClaim(
  claimText: string,
  sourceUrl: string,
  account: `0x${string}`,
) {
  const txHash = await client.writeContract({
    address: CONTRACT_ADDRESS,
    functionName: 'submit_claim',
    args: [claimText, sourceUrl],
    account,
  });
  return client.waitForTransactionReceipt({ hash: txHash });
}

/** Ask validators to resolve a claim that's already been submitted. */
export async function resolveClaim(claimId: number, account: `0x${string}`) {
  const txHash = await client.writeContract({
    address: CONTRACT_ADDRESS,
    functionName: 'resolve_claim',
    args: [claimId],
    account,
  });
  return client.waitForTransactionReceipt({ hash: txHash });
}

/** Read back a claim's current state (read-only, no gas). */
export async function getClaim(claimId: number) {
  return client.readContract({
    address: CONTRACT_ADDRESS,
    functionName: 'get_claim',
    args: [claimId],
  });
}

export async function totalClaims() {
  return client.readContract({
    address: CONTRACT_ADDRESS,
    functionName: 'total_claims',
    args: [],
  });
}
