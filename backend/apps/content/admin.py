from django.contrib import admin

from .models import Event, GalleryItem, Page, Testimonial


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "is_published")
    list_filter = ("is_published", "start_date")
    search_fields = ("title", "description", "location")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-start_date",)

@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "display_order", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    ordering = ("display_order", "-created_at")

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("student_name", "course_name", "rating", "is_published", "display_order")
    list_filter = ("is_published", "rating")
    search_fields = ("student_name", "course_name", "text")
    ordering = ("display_order", "-created_at")
