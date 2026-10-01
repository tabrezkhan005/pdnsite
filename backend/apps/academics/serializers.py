from rest_framework import serializers

from .models import Branch, Course, Faculty


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "slug", "address", "phone", "email", "map_url", "display_order"]

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "title", "slug", "description", "short_description", "duration", "monthly_fee", "image", "display_order"]

class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ["id", "name", "role", "bio", "image", "display_order"]
