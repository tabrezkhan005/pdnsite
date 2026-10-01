from rest_framework import serializers

from .models import Event, GalleryItem, Page, Testimonial


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "title", "slug", "content"]

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title", "slug", "description", "start_date", "end_date", "location", "image"]

class GalleryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryItem
        fields = ["id", "title", "image", "description", "display_order"]

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ["id", "student_name", "course_name", "text", "video_url", "image", "rating", "display_order"]
