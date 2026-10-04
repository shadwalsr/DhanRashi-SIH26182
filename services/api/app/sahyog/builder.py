"""SAHYOG Request Builder with statutory completeness validation (FR-SAH-02)."""

from typing import Any

MANDATORY_FIELDS = [
    ("case_id", "Case identifier is required"),
    ("investigation_id", "Investigation identifier is required"),
    ("report_id", "Approved attribution report identifier is required"),
    ("target_vasp_id", "Target VASP identifier is required"),
    ("target_vasp_name", "Target VASP entity name is required"),
    ("target_wallet_address", "Target wallet address is required"),
    ("reason", "Statutory justification / grounds for disclosure is required"),
    ("statutory_basis", "Legal authority / Section (e.g. Section 91 CrPC) is required"),
    ("officer_name", "Investigating officer name is required"),
    ("officer_designation", "Officer designation / rank is required"),
]


class SahyogRequestBuilder:
    """Builds and validates lawful disclosure requests from investigation case data (FR-SAH-02)."""

    @staticmethod
    def validate_request_data(payload: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validates all mandatory fields.
        Returns (is_valid, list_of_errors). Missing fields keep status DRAFT with error list.
        """
        errors: list[str] = []
        for field_name, err_msg in MANDATORY_FIELDS:
            val = payload.get(field_name)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(err_msg)

        # Address format check
        target_addr = payload.get("target_wallet_address", "")
        if target_addr and len(target_addr.strip()) < 10:
            errors.append("Target wallet address format is invalid")

        return len(errors) == 0, errors

    @staticmethod
    def build_reference_number(case_ref: str, vasp_id: str, seq: int = 1) -> str:
        """Generates a canonical statutory reference number."""
        clean_ref = case_ref.replace(" ", "-").upper()
        clean_vasp = vasp_id.replace(" ", "-").upper()
        return f"SAH-{clean_ref}-{clean_vasp}-{seq:03d}"
