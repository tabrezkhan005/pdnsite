import random
from datetime import date, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.academics.models import Batch, Branch, ClassSession, Course, Enrollment, Level
from apps.academics.services import enroll_student, generate_sessions
from apps.accounts.models import GuardianProfile, StaffProfile, StudentProfile, User
from apps.attendance.models import Attendance


class Command(BaseCommand):
    help = "Seeds the database with realistic demo data for development."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR("Refusing to seed data when DEBUG is False."))
            return

        self.stdout.write("Seeding database...")

        with transaction.atomic():
            self._clear_data()
            self._seed_data()

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("Demo credentials:"))
        self.stdout.write(self.style.SUCCESS("Admin: admin / admin"))
        self.stdout.write(self.style.SUCCESS("Staff (Teacher): staff / staff"))
        self.stdout.write(self.style.SUCCESS("Guardian: +919000000001 (OTP: 123456 via stub)"))
        self.stdout.write(self.style.SUCCESS("Student: student / student"))

    def _clear_data(self):
        User.objects.exclude(is_superuser=True).delete()
        Branch.objects.all().delete()
        Course.objects.all().delete()
        # Dependent objects cascade delete usually, but doing it safely.

    def _seed_data(self):
        # 1. Base entities
        branch_gnt = Branch.objects.create(name="Guntur", slug="gnt", code="GNT", address="Guntur Main")
        branch_hyd = Branch.objects.create(name="Hyderabad", slug="hyd", code="HYD", address="Hyd Branch")

        c1 = Course.objects.create(title="Kuchipudi Core", slug="kc", duration="1 year")
        c2 = Course.objects.create(title="Bharatanatyam Basics", slug="bb", duration="6 months")
        c3 = Course.objects.create(title="Carnatic Music", slug="cm", duration="1 year")

        l1 = Level.objects.create(course=c1, name="Beginner", order=1)
        Level.objects.create(course=c1, name="Intermediate", order=2)
        l3 = Level.objects.create(course=c2, name="Level 1", order=1)
        l4 = Level.objects.create(course=c3, name="Vocal 1", order=1)

        # 2. Staff (10)
        staff_profiles = []
        for i in range(10):
            u = User.objects.create_user(username=f"teacher{i}", role=User.Role.STAFF)
            u.set_password("staff")
            u.first_name = "Teacher"
            u.last_name = f"{i}"
            u.save()
            sp = StaffProfile.objects.create(user=u, branch=branch_gnt if i < 5 else branch_hyd, is_teacher=True)
            staff_profiles.append(sp)

        # Base roles
        admin = User.objects.create_superuser(username="admin", password="admin", email="admin@example.com", role=User.Role.ADMIN)
        admin.first_name = "System"
        admin.last_name = "Admin"
        admin.save()

        # Override the first staff to be the known 'staff' credential
        staff_profiles[0].user.username = "staff"
        staff_profiles[0].user.set_password("staff")
        staff_profiles[0].user.save()

        # 3. Batches (6)
        batches = []
        for i in range(6):
            b = Batch.objects.create(
                course=c1 if i < 3 else (c2 if i < 5 else c3),
                level=l1 if i < 3 else (l3 if i < 5 else l4),
                branch=branch_gnt if i % 2 == 0 else branch_hyd,
                teacher=staff_profiles[i],
                name=f"Batch {i+1}",
                days_of_week=[1, 3, 5], # Mon, Wed, Fri
                start_time=time(17, 0),
                end_time=time(18, 0),
                capacity=15,
                mode=Batch.Mode.OFFLINE
            )
            batches.append(b)

        # 4. Guardians and Students (30 students)
        students = []
        guardians = []
        for i in range(30):
            if i % 2 == 0:
                phone = f"+9190000000{i:02d}"
                gu = User.objects.create_user(username=f"guard{i}", role=User.Role.GUARDIAN, phone=phone)
                gu.set_password("password") # Normally guardians login via OTP
                gu.save()
                guardian = GuardianProfile.objects.create(user=gu)
                guardians.append(guardian)
            else:
                guardian = guardians[-1] # siblings

            student = StudentProfile.objects.create(
                full_name=f"Student {i}",
                guardian=guardian,
                branch=batches[i % 6].branch,
                student_id=f"PDN-{batches[i % 6].branch.code}-26-{i:04d}",
                date_of_birth=date(2010 + (i % 5), 1, 1)
            )
            students.append(student)

            # Enroll student in a batch
            enroll_student(student, batches[i % 6], admin)

        # Base role for guardian
        guardians[0].user.phone = "+919000000001"
        guardians[0].user.save()

        # Base role for student (student / student)
        stu_user = User.objects.create_user(username="student", role=User.Role.STUDENT)
        stu_user.set_password("student")
        stu_user.save()
        students[0].user = stu_user
        students[0].save()

        # 5. Month of sessions & attendance
        today = timezone.now().date()
        from_date = today - timedelta(days=30)
        to_date = today + timedelta(days=15)

        for batch in batches:
            generate_sessions(batch, from_date, to_date)

            # Add attendance for past sessions
            past_sessions = batch.sessions.filter(starts_at__date__lt=today, status=ClassSession.Status.SCHEDULED)
            past_sessions.update(status=ClassSession.Status.COMPLETED)

            for session in past_sessions:
                enrollments = batch.enrollments.filter(status=Enrollment.Status.ACTIVE)
                for e in enrollments:
                    status = random.choices(
                        [Attendance.Status.PRESENT, Attendance.Status.ABSENT, Attendance.Status.LATE],
                        weights=[80, 10, 10]
                    )[0]
                    Attendance.objects.create(
                        session=session,
                        student=e.student,
                        status=status,
                        source=Attendance.Source.MANUAL,
                        marked_by=batch.teacher.user
                    )
