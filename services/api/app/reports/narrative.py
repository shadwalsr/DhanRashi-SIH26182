"""Narrative generation and LLM grounding output validation (FR-AI-01, FR-AI-02, LLM-03)."""

import re
from typing import Any


class LLMValidationError(Exception):
    """Raised when LLM-generated narrative contains hallucinated entities, addresses, or hashes."""


def generate_template_narrative(context: dict[str, Any]) -> str:
    """Generates a professional, deterministic template narrative when LLM is off (FR-AI-02).
    Fully grounded on structured JSON facts.
    """
    case_ref = context.get("case_reference", "N/A")
    case_title = context.get("case_title", "Cryptocurrency Tracing Investigation")
    seed_wallet = context.get("target_wallet", "N/A")
    chain = context.get("blockchain", "N/A").capitalize()
    created_at = context.get("created_at", "N/A")

    top_vasp_name = context.get("top_vasp_name", "Unknown VASP")
    top_vasp_id = context.get("top_vasp_id", "VASP-UNKNOWN")
    final_score = context.get("final_score", 0.0)
    tier = context.get("tier", "INSUFFICIENT")
    raw_score = context.get("raw_score", 0.0)
    applied_caps = context.get("applied_caps", [])
    limitations = context.get("limitations", [])

    risk_score = context.get("risk_score", 0)
    risk_tier = context.get("risk_tier", "LOW")
    triggered_signals = context.get("triggered_signals", [])

    cross_chain_events = context.get("cross_chain_events", [])
    traced_usd = context.get("traced_usd", "0.00")
    total_nodes = context.get("total_nodes", 0)
    total_edges = context.get("total_edges", 0)

    # Section 1: Executive Summary
    lines = [
        "EXECUTIVE INVESTIGATION NARRATIVE",
        f"Case Reference: {case_ref} · Title: {case_title}",
        f"Generated: {created_at} UTC",
        "",
        "1. OVERVIEW & TARGET IDENTIFICATION",
        (
            f"An investigation was initiated on seed wallet {seed_wallet} on the {chain} network. "
            f"Automated graph tracing reconstructed a transaction flow topology spanning {total_nodes} nodes "
            f"and {total_edges} transfer edges, tracking cumulative funds of ${traced_usd} USD."
        ),
        "",
        "2. ENTITY ATTRIBUTION FINDINGS (FR-ATT-01..09)",
        (
            f"The multi-factor explainable attribution engine evaluated candidate destinations against the VASP intelligence registry. "
            f"The primary attributed Virtual Asset Service Provider is {top_vasp_name} ({top_vasp_id}) with an overall attribution "
            f"score of {final_score:.1%} (Confidence Tier: {tier})."
        ),
        f"Prior to deterministic cap evaluation, the raw mathematical correlation score was {raw_score:.4f}.",
    ]

    if applied_caps:
        lines.append("")
        lines.append("Applied Attribution Caps (PRD FR-ATT-04):")
        for cap in applied_caps:
            cap_code = cap.get("cap_code", "CAP")
            max_s = cap.get("max_score", 1.0)
            reason = cap.get("reason", "")
            lines.append(f" - [{cap_code}] Score capped at {max_s:.0%}: {reason}")

    # Section 3: Transit Laundering Risk Assessment
    lines.extend([
        "",
        "3. INDEPENDENT TRANSIT RISK ASSESSMENT (FR-RISK-01..04)",
        (
            f"Independent of entity attribution (AT-12 invariant), transit fund laundering indicators were evaluated along the flow trail. "
            f"Overall Transit Risk Score: {risk_score}/100 (Risk Tier: {risk_tier})."
        ),
    ])

    if triggered_signals:
        lines.append("Observed Laundering Risk Signals:")
        for s in triggered_signals:
            lines.append(f" - {s.get('name')}: {s.get('description')} (+{s.get('score')} pts)")
    else:
        lines.append(" - No high-risk laundering patterns (mixers or rapid peel chains) detected along the direct transit path.")

    lines.append(
        "Note on VASP Neutrality (FR-RISK-04): Regulated VASP terminal nodes receive zero risk score; "
        "risk scoring evaluates source obfuscation and intermediary transit hops only."
    )

    # Section 4: Cross-Chain Activity
    if cross_chain_events:
        lines.extend([
            "",
            "4. CROSS-CHAIN BRIDGE ACTIVITY (FR-XCH-01..05)",
            f"Detected {len(cross_chain_events)} cross-chain bridge interaction(s):",
        ])
        for ev in cross_chain_events:
            lines.append(
                f" - Bridge {ev.get('bridge_id')}: {ev.get('source_chain')} -> {ev.get('destination_chain')} "
                f"(Confidence: {ev.get('confidence', 0.0):.1%}, Ambiguous: {ev.get('is_ambiguous')})"
            )

    # Section 5: Epistemic Limitations & Disclaimers
    lines.extend([
        "",
        "5. MANDATORY LIMITATIONS & STATUTORY DISCLAIMER (FR-RPT-03)",
        (
            "Attribution results represent algorithmic inferences based on public distributed ledger data, "
            "heuristic clustering, and curated entity databases. This document serves as an investigative lead "
            "and does not constitute conclusive legal proof of wallet ownership or unlawful activity."
        ),
    ])

    if limitations:
        for lim in limitations:
            lines.append(f" - Limitation: {lim}")

    return "\n".join(lines)


def validate_llm_grounding(narrative_text: str, grounding_context: dict[str, Any]) -> None:
    """Validates that any LLM-generated narrative contains zero hallucinated addresses,
    transaction hashes, or VASP identifiers not present in the input grounding context (FR-AI-01, test LLM-03).
    """
    valid_addresses = {a.lower() for a in grounding_context.get("valid_addresses", [])}
    valid_hashes = {h.lower() for h in grounding_context.get("valid_hashes", [])}
    valid_vasps = {v.lower() for v in grounding_context.get("valid_vasps", [])}

    # 1. Check EVM addresses (0x[40 hex])
    evm_addresses = set(re.findall(r"\b(0x[a-fA-F0-9]{40})\b", narrative_text))
    for addr in evm_addresses:
        if addr.lower() not in valid_addresses:
            raise LLMValidationError(
                f"Grounding violation (LLM-03): Hallucinated EVM address detected in narrative: {addr}"
            )

    # 2. Check Tron addresses (T[33 base58])
    tron_addresses = set(re.findall(r"\b(T[1-9A-HJ-NP-Za-km-z]{33})\b", narrative_text))
    for addr in tron_addresses:
        if addr.lower() not in valid_addresses:
            raise LLMValidationError(
                f"Grounding violation (LLM-03): Hallucinated Tron address detected in narrative: {addr}"
            )

    # 3. Check transaction hashes (0x[64 hex])
    tx_hashes = set(re.findall(r"\b(0x[a-fA-F0-9]{64})\b", narrative_text))
    for h in tx_hashes:
        if h.lower() not in valid_hashes:
            raise LLMValidationError(
                f"Grounding violation (LLM-03): Hallucinated transaction hash detected in narrative: {h}"
            )

    # 4. Check VASP IDs (VASP-...)
    vasp_ids = set(re.findall(r"\b(VASP-[A-Za-z0-9_\-]+)\b", narrative_text))
    for vid in vasp_ids:
        if vid.lower() not in valid_vasps:
            raise LLMValidationError(
                f"Grounding violation (LLM-03): Hallucinated VASP ID detected in narrative: {vid}"
            )
