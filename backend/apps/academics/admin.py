from django.contrib import admin

from .models import Branch, Course, Faculty


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "duration", "monthly_fee", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "title")

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "address")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "role")
    ordering = ("display_order", "name")
