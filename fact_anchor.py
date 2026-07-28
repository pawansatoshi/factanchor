# { "Depends": "py-genlayer:test" }
from genlayer import *
import json


class ClaimStatus:
    UNRESOLVED = "unresolved"
    TRUE = "true"
    FALSE = "false"
    UNDETERMINED = "undetermined"  # evidence insufficient — a real, storable outcome


class FactAnchor(gl.Contract):
    """
    A reusable, web-grounded claim-resolution primitive.

    Anyone submits a plain-English, checkable claim (e.g. "Did the Fed cut
    rates on July 30 2026?"). Resolution runs the leader/validator pattern
    from GenLayer's Equivalence Principle: every validator independently
    fetches the same web source and asks its own LLM, then only the
    objective decision field (`verdict`) is compared across nodes — never
    the free-text reasoning, which will always be worded differently between
    validators. This is "Partial Field Matching" per GenLayer's docs, not a
    single strict_eq wrapper around one non-deterministic call — the leader's
    verdict is never trusted on its own; it is only accepted once a second,
    independently-computed verdict from a validator agrees with it.

    Designed to be called as a primitive, not just a standalone demo:
    a prediction market, parametric insurance contract, or an Internet
    Court-style dispute contract can call `resolve_claim` and read back a
    settled `verdict` instead of re-implementing web-grounded resolution
    logic itself.
    """

    claims: dict[int, str]
    source_urls: dict[int, str]
    statuses: dict[int, str]        # compared decision field
    reasonings: dict[int, str]      # uncompared free-text, stored for transparency
    next_id: int

    def __init__(self):
        self.claims = {}
        self.source_urls = {}
        self.statuses = {}
        self.reasonings = {}
        self.next_id = 0

    @gl.public.write
    def submit_claim(self, claim_text: str, source_url: str) -> int:
        """
        Register a new claim. `source_url` is the page validators will
        independently fetch to ground their judgment — required, since a
        claim with no fixed source can't be verified consistently across
        validators (that's what made the earlier google.com/search version
        of this contract non-reproducible between nodes).
        """
        claim_id = self.next_id
        self.claims[claim_id] = claim_text
        self.source_urls[claim_id] = source_url
        self.statuses[claim_id] = ClaimStatus.UNRESOLVED
        self.reasonings[claim_id] = ""
        self.next_id += 1
        return claim_id

    @gl.public.write
    def resolve_claim(self, claim_id: int) -> None:
        """
        Runs validator consensus on an already-submitted claim.

        Leader and validator each independently: fetch `source_url`, ask an
        LLM to extract {verdict, reasoning} from it. Only `verdict` is
        compared (Pattern 1: Partial Field Matching) — `reasoning` is stored
        from the accepted leader result but never used for consensus, since
        two LLMs will always phrase an explanation differently even when
        they agree on the fact.
        """
        if self.statuses[claim_id] != ClaimStatus.UNRESOLVED:
            raise gl.vm.UserError("[EXPECTED] claim already resolved")

        claim_text = self.claims[claim_id]
        source_url = self.source_urls[claim_id]

        def leader_fn() -> dict:
            web_data = gl.nondet.web.get(source_url)
            prompt = f"""
            You are a neutral fact-checker. Using ONLY the page content
            below, decide whether this claim is true, false, or
            undetermined (insufficient evidence on this page).

            Claim: "{claim_text}"

            Page content:
            {web_data.body[:4000]}

            Return JSON: {{"verdict": "true|false|undetermined", "reasoning": "<1-2 sentences>"}}
            """
            raw = gl.nondet.exec_prompt(prompt)
            return json.loads(raw)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                # Leader errored (e.g. source_url unreachable) — re-run and
                # require the validator to hit the same class of failure
                # before agreeing; otherwise reject and force a retry.
                try:
                    leader_fn()
                    return False
                except Exception:
                    return True

            validator_data = leader_fn()
            leader_data = leader_result.calldata

            # Only the decision field must match — reasoning text is allowed
            # to differ freely between independent LLM calls.
            return leader_data.get("verdict") == validator_data.get("verdict")

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        self.statuses[claim_id] = result.get("verdict", ClaimStatus.UNDETERMINED)
        self.reasonings[claim_id] = result.get("reasoning", "")

    @gl.public.view
    def get_claim(self, claim_id: int) -> dict:
        return {
            "claim": self.claims.get(claim_id, ""),
            "source_url": self.source_urls.get(claim_id, ""),
            "status": self.statuses.get(claim_id, ClaimStatus.UNRESOLVED),
            "reasoning": self.reasonings.get(claim_id, ""),
        }

    @gl.public.view
    def total_claims(self) -> int:
        return self.next_id
