from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BranchViewSet, CourseViewSet, FacultyViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'faculty', FacultyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
