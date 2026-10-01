from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GuardianProfile, StudentProfile, StaffProfile, AuditLog, ConsentRecord

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "phone", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "phone")


@admin.register(GuardianProfile)
class GuardianProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "relationship_note", "whatsapp_opt_in")
    search_fields = ("user__first_name", "user__last_name", "user__phone", "user__email")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "student_id", "branch", "status", "guardian")
    list_filter = ("status", "branch", "joined_on")
    search_fields = ("full_name", "student_id", "guardian__user__phone")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "is_teacher")
    list_filter = ("is_teacher", "branch")
    search_fields = ("user__first_name", "user__last_name", "user__phone")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_content_type", "ip_address", "created_at")
    list_filter = ("action", "created_at", "target_content_type")
    search_fields = ("action", "actor__username")
    readonly_fields = ("actor", "action", "target_content_type", "target_object_id", "before_state", "after_state", "ip_address")

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("guardian", "student", "consent_type", "granted", "source", "granted_at")
    list_filter = ("consent_type", "granted", "source")
    search_fields = ("guardian__user__first_name", "guardian__user__phone", "student__full_name")
