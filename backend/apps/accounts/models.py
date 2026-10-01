"""
Custom User model for Perin Devi Natyalayam.

This MUST be defined before the first migration is run.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user with UUID primary key, role, and phone number.

    Roles are used for coarse-grained access control:
    - ADMIN: full system access
    - STAFF: faculty and administrative staff
    - STUDENT: enrolled students
    - GUARDIAN: parents/guardians linked to students
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        STUDENT = "STUDENT", "Student"
        GUARDIAN = "GUARDIAN", "Guardian"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text="Phone number with country code, e.g. +919876543210",
    )

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
