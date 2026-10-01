from django.contrib import admin

from .models import AdmissionEnquiry, ContactMessage


@admin.register(AdmissionEnquiry)
class AdmissionEnquiryAdmin(admin.ModelAdmin):
    list_display = ("student_name", "phone", "course_interest", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("student_name", "parent_name", "email", "phone")
    ordering = ("-created_at",)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "subject")
    ordering = ("-created_at",)
