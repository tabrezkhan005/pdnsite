from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EventViewSet, GalleryItemViewSet, PageViewSet, TestimonialViewSet

router = DefaultRouter()
router.register(r'pages', PageViewSet)
router.register(r'events', EventViewSet)
router.register(r'gallery', GalleryItemViewSet)
router.register(r'testimonials', TestimonialViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
