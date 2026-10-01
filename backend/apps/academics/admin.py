from django.contrib import admin
from .models import Course, Branch, Faculty, Level, Batch, Enrollment, Holiday, ClassSession

class LevelInline(admin.TabularInline):
    model = Level
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "duration", "monthly_fee", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "title")
    inlines = [LevelInline]

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "phone", "email", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "code")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "role")
    ordering = ("display_order", "name")

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    raw_id_fields = ("student",)

class ClassSessionInline(admin.TabularInline):
    model = ClassSession
    extra = 0
    readonly_fields = ("status",)

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "level", "branch", "teacher", "mode", "capacity", "is_active")
    list_filter = ("is_active", "mode", "branch", "course")
    search_fields = ("name", "teacher__user__first_name", "teacher__user__last_name")
    raw_id_fields = ("teacher",)
    inlines = [EnrollmentInline, ClassSessionInline]

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "reason", "branch")
    list_filter = ("branch", "date")
    search_fields = ("reason",)

@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ("batch", "starts_at", "ends_at", "mode", "status", "is_makeup")
    list_filter = ("status", "mode", "is_makeup", "starts_at")
    search_fields = ("batch__name", "cancellation_reason", "notes")
    raw_id_fields = ("batch",)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "batch", "status", "enrolled_on", "ended_on")
    list_filter = ("status", "enrolled_on")
    search_fields = ("student__full_name", "student__student_id", "batch__name")
    raw_id_fields = ("student", "batch")
