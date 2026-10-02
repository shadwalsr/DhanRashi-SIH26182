export interface ValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
}

export function validateAddress(address: string, chain: string): ValidationResult {
  const cleanAddr = address.trim();
  if (!cleanAddr) {
    return { valid: false, error: "Wallet address is required." };
  }

  const normalizedChain = chain.toLowerCase();

  if (["ethereum", "polygon", "bnb_chain"].includes(normalizedChain)) {
    if (!/^0x[0-9a-fA-F]{40}$/.test(cleanAddr)) {
      return {
        valid: false,
        error: "Invalid EVM address. Must be a 42-character hex string starting with 0x.",
      };
    }
    if (/^0x0{40}$/i.test(cleanAddr)) {
      return {
        valid: false,
        error: "Zero address (0x0...0) is a burn/mint address and cannot be investigated.",
      };
    }
    return { valid: true };
  }

  if (normalizedChain === "tron") {
    if (!/^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(cleanAddr)) {
      return {
        valid: false,
        error: "Invalid Tron address. Must be a 34-character Base58Check string starting with 'T'.",
      };
    }
    return { valid: true };
  }

  if (normalizedChain === "bitcoin") {
    return {
      valid: true,
      warning: "Bitcoin provider is an architecture-only stub (P2). Synthetic fixtures will be used.",
    };
  }

  if (normalizedChain === "solana") {
    return {
      valid: true,
      warning: "Solana provider is an architecture-only stub (P2). Synthetic fixtures will be used.",
    };
  }

  return { valid: true };
}

export function validateDepth(depth: number): { warning?: string } {
  if (depth > 3) {
    return {
      warning:
        "Traces beyond depth 3 experience exponential branch expansion and may return PARTIAL subtrees due to rate/hop bounds.",
    };
  }
  return {};
}
