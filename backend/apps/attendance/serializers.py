from rest_framework import serializers

from apps.academics.models import ClassSession

from .models import Attendance, LeaveRequest


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "session", "student", "student_name", "status", "source", "marked_by", "marked_at", "note"]
        read_only_fields = ["source", "marked_by", "marked_at"]


class BulkAttendanceSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    # Actually wait, session id is usually in URL. We'll use a list of students
    attendances = serializers.ListField(
        child=serializers.DictField()
    )


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSession
        fields = ["id", "batch", "starts_at", "ends_at", "mode", "meeting_url", "status", "cancellation_reason", "notes", "is_makeup"]

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ["id", "student", "session", "from_date", "to_date", "reason", "status", "requested_by", "decided_by", "decided_at", "created_at"]
        read_only_fields = ["status", "requested_by", "decided_by", "decided_at", "created_at"]
