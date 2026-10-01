from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Attendance, SessionJoin, LeaveRequest
from apps.academics.models import ClassSession, Enrollment
from apps.accounts.services import log_audit_event

def get_attendance_status_for_join(session: ClassSession, join_time) -> str:
    """
    Determine if a join is ON TIME (PRESENT) or LATE.
    Late is defined as > 15 minutes after start.
    """
    late_threshold = session.starts_at + timedelta(minutes=15)
    if join_time > late_threshold:
        return Attendance.Status.LATE
    return Attendance.Status.PRESENT


def join_session(session: ClassSession, student, ip_address: str, user_agent: str, actor):
    """
    Record a session join for a student.
    Marks them PRESENT or LATE. Does not downgrade teacher mark.
    """
    now = timezone.now()
    
    # Enforce window: 10m before to end
    join_start = session.starts_at - timedelta(minutes=10)
    if now < join_start:
        raise ValueError("Session is not yet open for joining.")
    if now > session.ends_at:
        raise ValueError("Session has already ended.")
        
    # Check enrollment
    is_enrolled = Enrollment.objects.filter(
        student=student,
        batch=session.batch,
        status=Enrollment.Status.ACTIVE
    ).exists()
    if not is_enrolled:
        raise ValueError("Student is not enrolled in this batch.")

    with transaction.atomic():
        SessionJoin.objects.create(
            session=session,
            student=student,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        status = get_attendance_status_for_join(session, now)
        
        attendance, created = Attendance.objects.get_or_create(
            session=session,
            student=student,
            defaults={
                'status': status,
                'source': Attendance.Source.ONLINE_JOIN,
                'marked_by': actor,
                'marked_at': now
            }
        )
        
        if not created:
            # Never downgrade teacher mark, but upgrade if needed
            # E.g. If marked ABSENT by teacher, but they join, mark PRESENT or LATE
            # If already PRESENT, leave it alone.
            # If EXCUSED, don't overwrite? Or maybe overwrite? Usually joining overrides EXCUSED.
            if attendance.status in [Attendance.Status.ABSENT, Attendance.Status.EXCUSED]:
                attendance.status = status
                attendance.source = Attendance.Source.ONLINE_JOIN
                attendance.marked_by = actor
                attendance.marked_at = now
                attendance.save()
            elif attendance.status == Attendance.Status.LATE and status == Attendance.Status.PRESENT:
                attendance.status = status
                attendance.source = Attendance.Source.ONLINE_JOIN
                attendance.marked_by = actor
                attendance.marked_at = now
                attendance.save()
                
    return session.meeting_url


def approve_leave(leave: LeaveRequest, decided_by):
    with transaction.atomic():
        leave.status = LeaveRequest.Status.APPROVED
        leave.decided_by = decided_by
        leave.decided_at = timezone.now()
        leave.save()
        
        # Mark affected sessions EXCUSED
        if leave.session:
            sessions = [leave.session]
        else:
            sessions = ClassSession.objects.filter(
                batch__enrollments__student=leave.student,
                batch__enrollments__status=Enrollment.Status.ACTIVE,
                starts_at__date__gte=leave.from_date,
                starts_at__date__lte=leave.to_date,
                status=ClassSession.Status.SCHEDULED
            )
            
        for session in sessions:
            att, created = Attendance.objects.get_or_create(
                session=session,
                student=leave.student,
                defaults={
                    'status': Attendance.Status.EXCUSED,
                    'source': Attendance.Source.MANUAL,
                    'marked_by': decided_by
                }
            )
            if not created and att.status != Attendance.Status.EXCUSED:
                att.status = Attendance.Status.EXCUSED
                att.source = Attendance.Source.MANUAL
                att.marked_by = decided_by
                att.save()

    return leave


def get_attendance_summary(student, batch=None):
    """
    Returns summary stats for a student.
    """
    qs = Attendance.objects.filter(student=student, session__status=ClassSession.Status.COMPLETED)
    if batch:
        qs = qs.filter(session__batch=batch)
        
    total_sessions = qs.exclude(status=Attendance.Status.EXCUSED).count()
    if total_sessions == 0:
        return {"percentage": 100, "total": 0, "present": 0, "late": 0, "absent": 0, "excused": qs.filter(status=Attendance.Status.EXCUSED).count()}
        
    present = qs.filter(status=Attendance.Status.PRESENT).count()
    late = qs.filter(status=Attendance.Status.LATE).count()
    absent = qs.filter(status=Attendance.Status.ABSENT).count()
    excused = qs.filter(status=Attendance.Status.EXCUSED).count()
    
    # Late can be counted as present, but maybe weighted differently?
    # Usually late is present for percentage purposes, or 50%. Assuming 100% here.
    percentage = ((present + late) / total_sessions) * 100
    
    return {
        "percentage": round(percentage, 2),
        "total": total_sessions,
        "present": present,
        "late": late,
        "absent": absent,
        "excused": excused
    }
