import re

from app.core.errors import InvalidAddressException, UnsupportedChainException
from app.domain.enums import Chain

# Supported MVP chains
ENABLED_CHAINS: set[str] = {
    Chain.ETHEREUM.value,
    Chain.BNB_CHAIN.value,
    Chain.POLYGON.value,
    Chain.TRON.value,
}

EVM_CHAINS: set[str] = {
    Chain.ETHEREUM.value,
    Chain.BNB_CHAIN.value,
    Chain.POLYGON.value,
}

EVM_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")
EVM_ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TRON_REGEX = re.compile(r"^T[a-zA-Z0-9]{33}$")


def validate_chain_enabled(chain: str) -> None:
    """Verifies that the requested blockchain is enabled in this deployment."""
    if chain.lower() not in ENABLED_CHAINS:
        raise UnsupportedChainException(
            f"Chain '{chain}' is not supported or enabled in this deployment."
        )


def validate_wallet_address(address: str, chain: str) -> str:
    """Validates cryptocurrency address format according to target blockchain.
    Returns normalized address (lowercased for EVM, original for Tron).
    """
    validate_chain_enabled(chain)
    chain_lower = chain.lower()

    if chain_lower in EVM_CHAINS:
        if not EVM_REGEX.match(address):
            raise InvalidAddressException(
                f"Address '{address}' does not match standard EVM 40-hex-character format."
            )
        if address.lower() == EVM_ZERO_ADDRESS:
            raise InvalidAddressException("Zero address (0x0...0) cannot be used as target wallet.")
        return address.lower()

    elif chain_lower == Chain.TRON.value:
        if not TRON_REGEX.match(address):
            raise InvalidAddressException(
                f"Address '{address}' does not match standard Tron Base58 format (must start with 'T' and be 34 characters)."
            )
        return address

    raise UnsupportedChainException(f"Address validation not supported for chain '{chain}'.")
