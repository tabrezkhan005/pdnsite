from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SessionViewSet, JoinSessionView, LeaveRequestViewSet, AttendanceSummaryView

router = DefaultRouter()
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'leaves', LeaveRequestViewSet, basename='leave')

urlpatterns = [
    path('attendance/', include(router.urls)),
    path('attendance/sessions/<uuid:pk>/join/', JoinSessionView.as_view(), name='session-join'),
    path('attendance/summary/', AttendanceSummaryView.as_view(), name='attendance-summary'),
]
