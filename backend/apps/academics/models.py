from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class Branch(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    map_url = models.URLField(blank=True, help_text="Google Maps embed URL or link")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        verbose_name_plural = "Branches"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Course(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    duration = models.CharField(max_length=100, help_text="e.g., '6 months', '1 year'")
    # Monthly fee in paise (e.g. 150000 = ₹1500)
    monthly_fee = models.PositiveIntegerField(help_text="Fee in paise (e.g. 150000 = ₹1500)", null=True, blank=True)
    image = models.ImageField(upload_to="courses/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        ordering = ["display_order", "title"]

    def __str__(self):
        return self.title


class Faculty(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, help_text="e.g. 'Senior Instructor', 'Director'")
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to="faculty/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta(TimeStampedModel.Meta):
        verbose_name_plural = "Faculty"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
