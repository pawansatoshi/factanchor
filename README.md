# FactAnchor — a trustless fact-resolution Intelligent Contract
Deployed and live on Bradbury Testnet at 0xE1a4780dc431a16f41cf17F44F60a4A503e55cf0.
Built for **GenLayer** (testnet Bradbury). Submit a plain-English, checkable
claim; validators independently browse the live web, judge it with an LLM,
and GenLayer's Optimistic Democracy consensus settles on one answer — no
oracle, no centralized API to trust.

This is GenLayer's flagship use case ("Digital Jury") in its simplest form:
resolving real-world natural-language questions a normal smart contract has
no way to evaluate.

## Important context — read before you build toward an airdrop

GenLayer has **not confirmed a token or airdrop**. What's real is a public
points program (Builder / Validator / Community tracks) on the GenLayer
Portal, and deploying a working contract to testnet is a genuine, verifiable
Builder-track contribution — much higher signal than clicking Discord quests.
But there's no guarantee points convert to anything. Build this because it's
a legitimately interesting demo of the tech, not because a payout is promised.

## What's in this repo

- `contracts/fact_anchor.py` — the Intelligent Contract. `submit_claim`
  (with a required `source_url` — a fixed source every validator fetches,
  so the claim is verifiable consistently across nodes), `resolve_claim`,
  `get_claim`, `total_claims`.

  `resolve_claim` uses GenLayer's **"Partial Field Matching"** pattern
  (documented under the Equivalence Principle), not a single `strict_eq`
  wrapper: a `leader_fn` and `validator_fn` each independently fetch the
  source and prompt an LLM; only the objective `verdict` field is compared
  across nodes, while the free-text `reasoning` is stored but never used
  for consensus (two LLMs will always phrase an explanation differently
  even when they agree on the fact). The leader's answer is never trusted
  on its own — it's only accepted once a second, independently-computed
  verdict agrees with it.

  It's built as a **reusable primitive**: a prediction market, parametric
  insurance contract, or dispute-resolution contract (e.g. something built
  on the Internet Court stack) can call `resolve_claim` and read back a
  settled `verdict`, instead of re-implementing web-grounded resolution.

- `frontend/genlayer-client.ts` — a thin **GenLayerJS** wrapper for
  submitting claims, triggering resolution, and reading results from a
  frontend or script.

## Deploying it

1. **Install the GenLayer CLI and SDK** (Python 3.11+, Node 18+):
   ```bash
   pip install genlayer
   npm install genlayer-js
   ```
2. **Test locally first** in the Simulator/Studio (studio.genlayer.com) —
   upload `fact_anchor.py`, deploy it there, and call `submit_claim` /
   `resolve_claim` to watch validator consensus happen before spending any
   testnet gas.
3. **Get testnet GEN** from the GenLayer faucet (linked from the Portal) —
   needed to pay for deployment and contract calls on Bradbury.
4. **Deploy to testnet:**
   ```bash
   genlayer deploy --contract contracts/fact_anchor.py --network testnet
   ```
   This prints your deployed contract address — put it into
   `CONTRACT_ADDRESS` in `frontend/genlayer-client.ts`.
5. **Try it end-to-end:**
   ```ts
   import { submitClaim, resolveClaim, getClaim } from './genlayer-client';

   const id = await submitClaim(
     'Base has officially confirmed a native token launch',
     'https://www.base.org/blog', // a fixed source every validator can fetch
     myAccount,
   );
   await resolveClaim(id, myAccount);
   console.log(await getClaim(id));
   ```

## Submitting it on the GenLayer Portal (Builder → Intelligent Contracts)

The Portal's own category description warns against "basic examples,
hello-world contracts, simple storage, thin LLM wrappers, format-only
validators, boilerplate forks, or generic 'AI decides X' demos" — the
rewritten `resolve_claim` above is specifically designed to clear that bar
(real leader/validator split, a documented equivalence pattern, a stated
reuse case) rather than a one-off demo.

When filling out **Submit Contribution → Builder → Intelligent Contracts**:

- **Title**: something like "FactAnchor — reusable web-grounded claim
  resolution primitive"
- **Notes / Description**: describe what it does, and explicitly name the
  equivalence pattern used (Partial Field Matching / `run_nondet_unsafe`)
  and the reuse case (prediction markets, insurance, dispute resolution) —
  reviewers are checking for exactly these signals per the category text.
- **Evidence → GitHub Repository (required)**: push this repo public and
  paste its URL. Keeping this README in the repo lets reviewers see the
  design reasoning without reading the whole contract first.
- Complete the reCAPTCHA and submit.

## Also: the open "Star Internet Court Skill" task

Separately from this submission, there's a quick +50pt Builder task open on
your Portal — starring https://github.com/internet-court/internet-court-skill.
Unrelated to FactAnchor's review, but worth clearing while you're there:
open the repo, hit Star (top right, next to Fork), then back on the Portal
click "Complete →" on that task.

## Where this could go next

- **Prediction market resolution**: use `resolve_claim`'s verdict to settle
  a betting/prediction contract instead of just storing true/false.
- **Parametric insurance**: resolve claims like "did flight X get delayed
  3+ hours" and auto-trigger a payout contract.
- **Content moderation jury**: resolve disputed claims about a post/comment
  instead of relying on a single centralized moderator.

## Caveats

- Testnet only — GEN and any state here have no real value yet.
- LLM-based resolution isn't infallible; treat `resolve_claim`'s output as a
  best-effort consensus judgment, not ground truth, especially for anything
  with money attached in a real deployment.
- `eq_principle.strict_eq` requires validators' outputs to match exactly;
  for production use you'd likely want a looser comparability principle
  (check GenLayer's docs on `eq_principle` options) since LLM phrasing can
  vary even when the verdict agrees.
