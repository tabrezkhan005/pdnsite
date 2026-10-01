from django.contrib import admin

from .models import Attendance, LeaveRequest, SessionJoin


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "source", "marked_by", "marked_at")
    list_filter = ("status", "source", "marked_at")
    search_fields = ("student__full_name", "session__batch__name")
    raw_id_fields = ("student", "session", "marked_by")


@admin.register(SessionJoin)
class SessionJoinAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "joined_at", "ip_address")
    list_filter = ("joined_at",)
    search_fields = ("student__full_name", "session__batch__name", "ip_address")
    raw_id_fields = ("student", "session")
    readonly_fields = ("joined_at",)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "from_date", "to_date", "status", "requested_by")
    list_filter = ("status", "from_date")
    search_fields = ("student__full_name", "reason")
    raw_id_fields = ("student", "session", "requested_by", "decided_by")
