from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("verification_code", "student_name", "course_name", "issue_date", "is_active")
    list_filter = ("is_active", "issue_date", "course_name")
    search_fields = ("verification_code", "student_name", "course_name")
    ordering = ("-issue_date", "student_name")
    readonly_fields = ("verification_code",)
