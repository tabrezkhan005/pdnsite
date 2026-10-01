from rest_framework import permissions, viewsets

from .models import Event, GalleryItem, Page, Testimonial
from .serializers import (
    EventSerializer,
    GalleryItemSerializer,
    PageSerializer,
    TestimonialSerializer,
)


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve published pages.
    """
    queryset = Page.objects.filter(is_published=True)
    serializer_class = PageSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve published events.
    """
    queryset = Event.objects.filter(is_published=True)
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

class GalleryItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve published gallery items.
    """
    queryset = GalleryItem.objects.filter(is_published=True)
    serializer_class = GalleryItemSerializer
    permission_classes = [permissions.AllowAny]

class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to list and retrieve published testimonials.
    """
    queryset = Testimonial.objects.filter(is_published=True)
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]
