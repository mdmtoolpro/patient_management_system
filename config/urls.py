from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('patients/', include('patients.urls')),
    path('laboratory/', include('laboratory.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('billing/', include('billing.urls')),
    path('users/', include('users.urls')),
    path('reports/', include('reports.urls')), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)