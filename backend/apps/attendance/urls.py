from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AttendanceSummaryView, JoinSessionView, LeaveRequestViewSet, SessionViewSet

router = DefaultRouter()
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'leaves', LeaveRequestViewSet, basename='leave')

urlpatterns = [
    path('attendance/', include(router.urls)),
    path('attendance/sessions/<uuid:pk>/join/', JoinSessionView.as_view(), name='session-join'),
    path('attendance/summary/', AttendanceSummaryView.as_view(), name='attendance-summary'),
]
