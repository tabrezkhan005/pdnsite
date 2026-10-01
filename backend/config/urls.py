"""
URL configuration for Perin Devi Natyalayam.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    """Health-check endpoint — verifies database connectivity."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok", "database": "connected"})
    except Exception as exc:
        return JsonResponse(
            {"status": "error", "database": str(exc)},
            status=503,
        )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    # OpenAPI schema and Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # API endpoints
    path("api/academics/", include("apps.academics.urls")),
    path("api/content/", include("apps.content.urls")),
    path("api/communications/", include("apps.communications.urls")),
    path("api/certificates/", include("apps.certificates.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "Perin Devi Natyalayam Admin"
admin.site.site_title = "PDN Admin"
admin.site.index_title = "Administration"
