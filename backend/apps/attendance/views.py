from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, status, views, response
from rest_framework.decorators import action
from .models import Attendance, LeaveRequest
from apps.academics.models import ClassSession, Enrollment
from apps.accounts.services import log_audit_event
from .serializers import AttendanceSerializer, BulkAttendanceSerializer, LeaveRequestSerializer
from .services import join_session, approve_leave, get_attendance_summary

class TeacherSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Teacher can see their sessions.
    GET /api/v1/attendance/sessions/
    GET /api/v1/attendance/sessions/{id}/roster/
    POST /api/v1/attendance/sessions/{id}/bulk_mark/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == "STAFF" and hasattr(user, 'staff_profile'):
            return ClassSession.objects.filter(batch__teacher=user.staff_profile)
        return ClassSession.objects.none()

    @action(detail=True, methods=['get'])
    def roster(self, request, pk=None):
        session = self.get_object()
        
        # Get active enrollments for the batch at the time of the session
        # For simplicity, we just check current ACTIVE status, but ideally
        # we check if enrolled_on <= session.date and (ended_on >= session.date or null)
        # Assuming current active enrollments:
        enrollments = Enrollment.objects.filter(batch=session.batch, status=Enrollment.Status.ACTIVE)
        
        attendances = Attendance.objects.filter(session=session)
        attendance_map = {a.student_id: a for a in attendances}
        
        roster_data = []
        for en in enrollments:
            student = en.student
            att = attendance_map.get(student.id)
            roster_data.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "status": att.status if att else None,
                "note": att.note if att else "",
            })
            
        return response.Response(roster_data)

    @action(detail=True, methods=['post'])
    def bulk_mark(self, request, pk=None):
        session = self.get_object()
        user = request.user
        
        # Edit window: allowed within 48 hours of session end. Admin override ignores this.
        window_end = session.ends_at + timedelta(hours=48)
        is_admin = user.role == "ADMIN"
        
        if not is_admin and timezone.now() > window_end:
            return response.Response({"detail": "Edit window closed. Contact admin."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        attendances = serializer.validated_data["attendances"]
        
        from django.db import transaction
        with transaction.atomic():
            for att_data in attendances:
                student_id = att_data["student_id"]
                att_status = att_data["status"]
                note = att_data.get("note", "")
                
                att, created = Attendance.objects.get_or_create(
                    session=session,
                    student_id=student_id,
                    defaults={
                        'status': att_status,
                        'source': Attendance.Source.ADMIN_OVERRIDE if is_admin and timezone.now() > window_end else Attendance.Source.MANUAL,
                        'marked_by': user,
                        'note': note
                    }
                )
                
                if not created:
                    before = {"status": att.status, "note": att.note}
                    att.status = att_status
                    att.note = note
                    att.source = Attendance.Source.ADMIN_OVERRIDE if is_admin and timezone.now() > window_end else Attendance.Source.MANUAL
                    att.marked_by = user
                    att.save()
                    
                    if is_admin and timezone.now() > window_end:
                        log_audit_event(
                            actor=user,
                            action="ADMIN_OVERRIDE_ATTENDANCE",
                            target=att,
                            before_state=before,
                            after_state={"status": att.status, "note": att.note}
                        )
                        
        return response.Response({"detail": "Attendance marked successfully."})


class JoinSessionView(views.APIView):
    """
    POST /api/v1/attendance/sessions/{id}/join/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        session = get_object_or_404(ClassSession, pk=pk)
        
        user = request.user
        if user.role != "STUDENT" or not hasattr(user, 'student_profile'):
            return response.Response({"detail": "Only students can join sessions online."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            url = join_session(
                session=session,
                student=user.student_profile,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                actor=user
            )
            return response.Response({"meeting_url": url})
        except ValueError as e:
            return response.Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    Leave requests endpoints.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LeaveRequestSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == "STUDENT" and hasattr(user, 'student_profile'):
            return LeaveRequest.objects.filter(student=user.student_profile)
        if user.role == "GUARDIAN" and hasattr(user, 'guardian_profile'):
            return LeaveRequest.objects.filter(student__guardian=user.guardian_profile)
        if user.role in ["STAFF", "ADMIN"]:
            return LeaveRequest.objects.all()
        return LeaveRequest.objects.none()
        
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(requested_by=user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        user = request.user
        if user.role not in ["STAFF", "ADMIN"]:
            return response.Response(status=status.HTTP_403_FORBIDDEN)
            
        leave = self.get_object()
        if leave.status != LeaveRequest.Status.PENDING:
            return response.Response({"detail": "Leave request already decided."}, status=status.HTTP_400_BAD_REQUEST)
            
        approve_leave(leave, user)
        return response.Response({"detail": "Leave request approved."})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        user = request.user
        if user.role not in ["STAFF", "ADMIN"]:
            return response.Response(status=status.HTTP_403_FORBIDDEN)
            
        leave = self.get_object()
        leave.status = LeaveRequest.Status.REJECTED
        leave.decided_by = user
        leave.decided_at = timezone.now()
        leave.save()
        return response.Response({"detail": "Leave request rejected."})


class AttendanceSummaryView(views.APIView):
    """
    GET /api/v1/attendance/summary/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if user.role == "STUDENT" and hasattr(user, 'student_profile'):
            student = user.student_profile
            summary = get_attendance_summary(student)
            return response.Response(summary)
        return response.Response({"detail": "Not a student."}, status=status.HTTP_400_BAD_REQUEST)
