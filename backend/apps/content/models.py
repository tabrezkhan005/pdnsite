from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class Page(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    is_published = models.BooleanField(default=False)

    class Meta(TimeStampedModel.Meta):
        ordering = ["title"]

    def __str__(self):
        return self.title


class Event(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    is_published = models.BooleanField(default=False)

    class Meta(TimeStampedModel.Meta):
        ordering = ["-start_date"]

    def __str__(self):
        return self.title


class GalleryItem(TimeStampedModel):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="gallery/")
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.title


class Testimonial(TimeStampedModel):
    student_name = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    video_url = models.URLField(blank=True, help_text="Optional YouTube/Vimeo link")
    image = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    rating = models.PositiveSmallIntegerField(default=5, help_text="Rating out of 5")
    is_published = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return f"Testimonial from {self.student_name}"
