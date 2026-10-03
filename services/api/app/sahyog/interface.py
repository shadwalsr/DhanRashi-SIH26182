"""SahyogProvider protocol declaring the 7 statutory lawful disclosure operations (FR-SAH-01)."""

from typing import Any, Protocol


class SahyogProvider(Protocol):
    """Protocol defining the 7 standard statutory operations for law enforcement/FIU interaction with VASPs."""

    name: str
    is_mock: bool

    async def create_disclosure_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Operation 1: Create a statutory disclosure request (e.g. Section 91 CrPC / Section 94 BNSS)."""
        ...

    async def create_freeze_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Operation 2: Issue an emergency debit freeze directive to the VASP."""
        ...

    async def get_request_status(self, reference_number: str) -> dict[str, Any]:
        """Operation 3: Query current tracking status of a submitted request."""
        ...

    async def list_requests(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Operation 4: List all requests for the organization unit."""
        ...

    async def upload_attachment(
        self,
        reference_number: str,
        filename: str,
        content: bytes,
        sha256_hash: str,
    ) -> dict[str, Any]:
        """Operation 5: Upload supporting legal orders or approved report PDFs with SHA-256 integrity verification."""
        ...

    async def cancel_request(self, reference_number: str, reason: str) -> dict[str, Any]:
        """Operation 6: Cancel or withdraw a pending statutory request."""
        ...

    async def get_vasp_compliance_info(self, vasp_id: str) -> dict[str, Any]:
        """Operation 7: Query VASP nodal officer, grievance contacts, and supported statutory formats."""
        ...
