from rest_framework import permissions, viewsets

from .models import Branch, Course, Faculty
from .serializers import BranchSerializer, CourseSerializer, FacultySerializer


class BranchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve active branches.
    """
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve active courses.
    """
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve active faculty members.
    """
    queryset = Faculty.objects.filter(is_active=True)
    serializer_class = FacultySerializer
    permission_classes = [permissions.AllowAny]
