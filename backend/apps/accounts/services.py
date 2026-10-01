from typing import Any

from django.contrib.contenttypes.models import ContentType

from .models import AuditLog, ConsentRecord


def log_audit_event(
    actor: Any,
    action: str,
    target: Any = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    ip_address: str | None = None
) -> AuditLog:
    """
    Helper function to record audit logs.
    actor should be a User instance or None (for system actions).
    target should be a Django model instance.
    """
    content_type = ContentType.objects.get_for_model(target) if target else None
    object_id = str(target.pk) if target else None

    # Handle anon users or system actor
    if actor and not actor.is_authenticated:
        actor = None

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_content_type=content_type,
        target_object_id=object_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address
    )


def record_consent(
    guardian,
    consent_type: str,
    granted: bool,
    source: str,
    student=None,
    ip_address: str | None = None
) -> ConsentRecord:
    """
    Service to record or revoke consent.
    """
    return ConsentRecord.objects.create(
        guardian=guardian,
        student=student,
        consent_type=consent_type,
        granted=granted,
        source=source,
        ip_address=ip_address
    )
