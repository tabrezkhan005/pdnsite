from datetime import timedelta, date, datetime
from typing import List
from django.db import transaction, models
from django.utils import timezone
from .models import Batch, ClassSession, Holiday, Enrollment
from apps.accounts.services import log_audit_event
from django.db.models import Count

def generate_sessions(batch: Batch, from_date: date, to_date: date) -> List[ClassSession]:
    """
    Idempotent function to generate class sessions for a batch within a date range,
    skipping holidays.
    """
    if from_date > to_date:
        return []
        
    holidays = set(
        Holiday.objects.filter(
            date__range=[from_date, to_date]
        ).filter(
            models.Q(branch=batch.branch) | models.Q(branch__isnull=True)
        ).values_list('date', flat=True)
    )
    
    current_date = from_date
    created_sessions = []
    
    # Days of week in python datetime: Monday is 0, Sunday is 6
    # Same as what we store in batch.days_of_week
    
    with transaction.atomic():
        while current_date <= to_date:
            if current_date.weekday() in batch.days_of_week and current_date not in holidays:
                # Create naive datetime from date and time, then make aware
                starts_at = timezone.make_aware(
                    datetime.combine(current_date, batch.start_time)
                )
                ends_at = timezone.make_aware(
                    datetime.combine(current_date, batch.end_time)
                )
                
                session, created = ClassSession.objects.get_or_create(
                    batch=batch,
                    starts_at=starts_at,
                    defaults={
                        'ends_at': ends_at,
                        'mode': batch.mode,
                        'meeting_url': batch.default_meeting_url,
                        'status': ClassSession.Status.SCHEDULED
                    }
                )
                if created:
                    created_sessions.append(session)
            current_date += timedelta(days=1)
            
    return created_sessions


def cancel_session(session: ClassSession, actor, reason: str) -> ClassSession:
    with transaction.atomic():
        before_state = {"status": session.status, "cancellation_reason": session.cancellation_reason}
        session.status = ClassSession.Status.CANCELLED
        session.cancellation_reason = reason
        session.save()
        after_state = {"status": session.status, "cancellation_reason": session.cancellation_reason}
        
        log_audit_event(
            actor=actor,
            action="CANCEL_SESSION",
            target=session,
            before_state=before_state,
            after_state=after_state
        )
    return session


def reschedule_session(session: ClassSession, actor, new_starts_at: datetime, new_ends_at: datetime, reason: str) -> ClassSession:
    with transaction.atomic():
        before_state = {"starts_at": session.starts_at.isoformat(), "ends_at": session.ends_at.isoformat(), "notes": session.notes}
        session.starts_at = new_starts_at
        session.ends_at = new_ends_at
        session.notes = f"{session.notes}\nRescheduled: {reason}".strip()
        session.save()
        after_state = {"starts_at": session.starts_at.isoformat(), "ends_at": session.ends_at.isoformat(), "notes": session.notes}
        
        log_audit_event(
            actor=actor,
            action="RESCHEDULE_SESSION",
            target=session,
            before_state=before_state,
            after_state=after_state
        )
    return session


def enroll_student(student, batch: Batch, actor) -> Enrollment:
    with transaction.atomic():
        # Lock batch row to prevent race conditions on capacity
        locked_batch = Batch.objects.select_for_update().get(id=batch.id)
        
        active_enrollments = Enrollment.objects.filter(batch=locked_batch, status=Enrollment.Status.ACTIVE).count()
        if active_enrollments >= locked_batch.capacity:
            raise ValueError(f"Batch {locked_batch.name} is full.")
            
        enrollment = Enrollment.objects.create(
            student=student,
            batch=locked_batch,
            status=Enrollment.Status.ACTIVE
        )
        
        log_audit_event(
            actor=actor,
            action="ENROLL_STUDENT",
            target=enrollment,
            after_state={"student": str(student.id), "batch": str(locked_batch.id), "status": enrollment.status}
        )
    return enrollment


def transfer_batch(enrollment: Enrollment, new_batch: Batch, actor) -> Enrollment:
    with transaction.atomic():
        locked_new_batch = Batch.objects.select_for_update().get(id=new_batch.id)
        
        active_enrollments = Enrollment.objects.filter(batch=locked_new_batch, status=Enrollment.Status.ACTIVE).count()
        if active_enrollments >= locked_new_batch.capacity:
            raise ValueError(f"Target batch {locked_new_batch.name} is full.")
            
        before_state = {"batch": str(enrollment.batch.id), "status": enrollment.status}
        
        # End old enrollment
        enrollment.status = Enrollment.Status.ENDED
        enrollment.ended_on = timezone.now().date()
        enrollment.save()
        
        # Create new enrollment
        new_enrollment = Enrollment.objects.create(
            student=enrollment.student,
            batch=locked_new_batch,
            status=Enrollment.Status.ACTIVE
        )
        
        log_audit_event(
            actor=actor,
            action="TRANSFER_BATCH",
            target=enrollment.student,
            before_state=before_state,
            after_state={"batch": str(locked_new_batch.id), "status": "ACTIVE"}
        )
    return new_enrollment


def change_student_status(student, new_status, actor):
    with transaction.atomic():
        before_state = {"status": student.status}
        student.status = new_status
        student.save()
        
        # If student becomes inactive or alumni, perhaps we should end active enrollments?
        # Leaving that as a domain decision. We'll end them to free capacity.
        if new_status in [student.Status.INACTIVE, student.Status.ALUMNI]:
            active_enrollments = Enrollment.objects.filter(student=student, status=Enrollment.Status.ACTIVE)
            for en in active_enrollments:
                en.status = Enrollment.Status.ENDED
                en.ended_on = timezone.now().date()
                en.save()
                
        after_state = {"status": student.status}
        log_audit_event(
            actor=actor,
            action="CHANGE_STUDENT_STATUS",
            target=student,
            before_state=before_state,
            after_state=after_state
        )
    return student
