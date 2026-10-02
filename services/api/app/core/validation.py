import hashlib
import re

from app.core.errors import InvalidAddressException, UnsupportedChainException
from app.domain.enums import Chain
from app.domain.models import AddressValidation

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
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Keccak-256 constants for pure Python EIP-55 checksum calculation
_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_KECCAK_ROTC = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def _rol(val: int, shift: int) -> int:
    return ((val << shift) | (val >> (64 - shift))) & 0xFFFFFFFFFFFFFFFF


def keccak_256(data: bytes) -> bytes:
    """Pure-Python Keccak-256 implementation (used for EIP-55 checksumming)."""
    state = [[0] * 5 for _ in range(5)]
    rate = 136  # 1088 bits / 8

    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != (rate - 1):
        padded.append(0x00)
    padded.append(0x80)

    for b in range(0, len(padded), rate):
        block = padded[b: b + rate]
        for i in range(17):
            idx_x = (i * 8) // 8 % 5
            idx_y = ((i * 8) // 40)
            word = int.from_bytes(block[i * 8: (i + 1) * 8], "little")
            state[idx_x][idx_y] ^= word

        for r in range(24):
            c_vals = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            d_vals = [c_vals[(x - 1) % 5] ^ _rol(c_vals[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= d_vals[x]

            b_vals = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    b_vals[y][(2 * x + 3 * y) % 5] = _rol(state[x][y], _KECCAK_ROTC[x][y])

            for x in range(5):
                for y in range(5):
                    state[x][y] = b_vals[x][y] ^ ((~b_vals[(x + 1) % 5][y]) & b_vals[(x + 2) % 5][y])

            state[0][0] ^= _KECCAK_RC[r]

    out = bytearray()
    for y in range(5):
        for x in range(5):
            out.extend(state[x][y].to_bytes(8, "little"))
            if len(out) >= 32:
                return bytes(out[:32])
    return bytes(out[:32])


def to_eip55_checksum(address: str) -> str:
    """Computes standard EIP-55 mixed-case checksum for an EVM address."""
    clean_addr = address.lower().removeprefix("0x")
    khash = keccak_256(clean_addr.encode("ascii")).hex()
    checksummed = "0x" + "".join(
        c.upper() if c.isalpha() and int(khash[i], 16) >= 8 else c.lower()
        for i, c in enumerate(clean_addr)
    )
    return checksummed


def _decode_base58(s: str) -> bytes:
    val = 0
    for c in s:
        idx = BASE58_ALPHABET.find(c)
        if idx == -1:
            raise ValueError(f"Invalid Base58 character: {c}")
        val = val * 58 + idx
    full = val.to_bytes((val.bit_length() + 7) // 8, "big") if val > 0 else b""
    num_zeros = len(s) - len(s.lstrip("1"))
    return b"\x00" * num_zeros + full


def validate_tron_base58check(address: str) -> bool:
    """Validates that a Tron address is valid Base58Check with 0x41 version byte."""
    if not TRON_REGEX.match(address):
        return False
    try:
        raw = _decode_base58(address)
        if len(raw) != 25:
            return False
        if raw[0] != 0x41:  # Tron mainnet address version byte
            return False
        payload = raw[:21]
        checksum = raw[21:]
        expected_checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return checksum == expected_checksum
    except (ValueError, IndexError):
        return False


def validate_chain_enabled(chain: str) -> None:
    """Verifies that the requested blockchain is enabled in this deployment."""
    if chain.lower() not in ENABLED_CHAINS:
        raise UnsupportedChainException(
            f"Chain '{chain}' is not supported or enabled in this deployment."
        )


def validate_wallet_address(address: str, chain: str) -> str:
    """Validates cryptocurrency address format according to target blockchain.
    Enforces EIP-55 for mixed-case EVM addresses, rejects EVM zero-address,
    and validates Tron Base58Check with 0x41 version byte.
    Returns normalized address (lowercased for EVM, exact Base58 for Tron).
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

        # Check if address is mixed case: if so, verify EIP-55 checksum
        clean_hex = address[2:]
        has_upper = any(c.isupper() for c in clean_hex if c.isalpha())
        has_lower = any(c.islower() for c in clean_hex if c.isalpha())

        if has_upper and has_lower:
            expected_checksum = to_eip55_checksum(address)
            if address != expected_checksum:
                raise InvalidAddressException(
                    f"Address '{address}' failed EIP-55 checksum verification."
                )

        return address.lower()

    elif chain_lower == Chain.TRON.value:
        if not validate_tron_base58check(address):
            raise InvalidAddressException(
                f"Address '{address}' is not a valid Tron Base58Check address (must start with 'T' and pass 0x41 checksum)."
            )
        return address

    raise UnsupportedChainException(f"Address validation not supported for chain '{chain}'.")


def normalize_address_for_chain(chain: str, address: str) -> str:
    """Normalizes address based on blockchain rules."""
    chain_lower = chain.lower()
    if chain_lower == Chain.TRON.value:
        return address
    return address.lower()


def validate_address_full(chain: str, address: str) -> AddressValidation:
    """Returns structured AddressValidation model per PRD §9.2."""
    try:
        norm = validate_wallet_address(address, chain)
        return AddressValidation(
            valid=True,
            normalized=norm,
            reason=None,
            kind="unknown",
        )
    except (InvalidAddressException, UnsupportedChainException) as e:
        return AddressValidation(
            valid=False,
            normalized=address,
            reason=e.message,
            kind="unknown",
        )
