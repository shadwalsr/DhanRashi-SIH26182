from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import NotFoundException
from app.core.rbac import require_permission
from app.db.models import ReportModel, User
from app.db.session import get_db
from app.domain.enums import AuditOutcome
from app.domain.models import ReportApprovalRequest, ReportCreate, ReportRead
from app.reports.engine import ReportEngine
from app.reports.pdf import generate_investigation_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: ReportCreate,
    current_user: User = Depends(require_permission("report.generate")),
    session: AsyncSession = Depends(get_db),
):
    """Generates an attribution and disclosure report, verifies epistemic fact labels, and creates PDF."""
    engine = ReportEngine(session)
    report = await engine.generate_report(
        case_id=payload.case_id,
        investigation_id=payload.investigation_id,
        title=payload.title,
        author=current_user,
    )
    return ReportRead.model_validate(report)


@router.get("", response_model=list[ReportRead])
async def list_reports(
    case_id: UUID | None = Query(None),
    current_user: User = Depends(require_permission("report.download")),
    session: AsyncSession = Depends(get_db),
):
    """Lists generated reports for a case or user scope."""
    stmt = select(ReportModel).order_by(ReportModel.created_at.desc())
    if case_id:
        stmt = stmt.where(ReportModel.case_id == case_id)
    res = await session.execute(stmt)
    return [ReportRead.model_validate(r) for r in res.scalars().all()]


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(require_permission("report.download")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves report metadata by ID."""
    stmt = select(ReportModel).where(ReportModel.id == report_id)
    res = await session.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundException(f"Report {report_id} not found")
    return ReportRead.model_validate(report)


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: UUID,
    current_user: User = Depends(require_permission("report.download")),
    session: AsyncSession = Depends(get_db),
):
    """Generates and downloads the PDF report with X-Report-SHA256 checksum header."""
    stmt = select(ReportModel).where(ReportModel.id == report_id)
    res = await session.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise NotFoundException(f"Report {report_id} not found")

    pdf_bytes, sha256_hash = generate_investigation_pdf(report.data_payload)

    await log_audit_event(
        session=session,
        action="REPORT_DOWNLOAD",
        resource_type="report",
        outcome=AuditOutcome.ALLOW,
        user_id=current_user.id,
        resource_id=str(report.id),
        details={"pdf_hash": sha256_hash},
    )
    await session.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="vasp-trace-report-{report.id}.pdf"',
            "X-Report-SHA256": sha256_hash,
        },
    )


@router.post("/{report_id}/approve", response_model=ReportRead)
async def approve_report(
    report_id: UUID,
    payload: ReportApprovalRequest,
    current_user: User = Depends(require_permission("report.approve")),
    session: AsyncSession = Depends(get_db),
):
    """Supervisory approval of attribution report (FR-RPT-04). Enforces separation of duties."""
    engine = ReportEngine(session)
    approved_report = await engine.approve_report(
        report_id=report_id,
        approver=current_user,
        comment=payload.comment,
    )
    return ReportRead.model_validate(approved_report)
