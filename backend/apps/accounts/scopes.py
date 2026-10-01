
def scope_students(queryset, user):
    """
    Admin: all
    Staff: students enrolled in their active batches
    Guardian: linked students
    Student: self
    """
    if user.role == "ADMIN":
        return queryset
    if user.role == "STAFF" and hasattr(user, "staff_profile"):
        # Students enrolled in batches taught by this staff
        # Optionally, restrict to ACTIVE enrollments only if strict
        return queryset.filter(enrollments__batch__teacher=user.staff_profile).distinct()
    if user.role == "GUARDIAN" and hasattr(user, "guardian_profile"):
        return queryset.filter(guardian=user.guardian_profile)
    if user.role == "STUDENT" and hasattr(user, "student_profile"):
        return queryset.filter(id=user.student_profile.id)
    return queryset.none()

def scope_batches(queryset, user):
    """
    Admin: all
    Staff: batches they teach
    Guardian: batches their students are enrolled in
    Student: batches they are enrolled in
    """
    if user.role == "ADMIN":
        return queryset
    if user.role == "STAFF" and hasattr(user, "staff_profile"):
        return queryset.filter(teacher=user.staff_profile)
    if user.role == "GUARDIAN" and hasattr(user, "guardian_profile"):
        return queryset.filter(enrollments__student__guardian=user.guardian_profile).distinct()
    if user.role == "STUDENT" and hasattr(user, "student_profile"):
        return queryset.filter(enrollments__student=user.student_profile)
    return queryset.none()

def scope_sessions(queryset, user):
    if user.role == "ADMIN":
        return queryset
    if user.role == "STAFF" and hasattr(user, "staff_profile"):
        return queryset.filter(batch__teacher=user.staff_profile)
    if user.role == "GUARDIAN" and hasattr(user, "guardian_profile"):
        return queryset.filter(batch__enrollments__student__guardian=user.guardian_profile).distinct()
    if user.role == "STUDENT" and hasattr(user, "student_profile"):
        return queryset.filter(batch__enrollments__student=user.student_profile).distinct()
    return queryset.none()

def scope_leaves(queryset, user):
    if user.role == "ADMIN":
        return queryset
    if user.role == "STAFF" and hasattr(user, "staff_profile"):
        # Leaves for students in their batches
        return queryset.filter(student__enrollments__batch__teacher=user.staff_profile).distinct()
    if user.role == "GUARDIAN" and hasattr(user, "guardian_profile"):
        return queryset.filter(student__guardian=user.guardian_profile)
    if user.role == "STUDENT" and hasattr(user, "student_profile"):
        return queryset.filter(student=user.student_profile)
    return queryset.none()
