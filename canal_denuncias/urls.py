from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from denuncias import views as denuncias_views
urlpatterns = [path('', RedirectView.as_view(pattern_name='denuncias:home'), name='root_redirect'), path('consultar-denuncia/', RedirectView.as_view(pattern_name='denuncias:lookup_complaint'), name='lookup_redirect'), path('denuncias/', include(('denuncias.urls', 'denuncias'), namespace='denuncias')), path('django-admin/', admin.site.urls)]
urlpatterns += [
    path('denuncias/consultar-denuncia/', denuncias_views.public_lookup_complaint, name='lookup_complaint'),
    path('denuncias/enviar-denuncia/', denuncias_views.public_submit_complaint, name='submit_complaint'),
    path('denuncias/admin/login/', denuncias_views.admin_login, name='admin_login'),
    path('denuncias/admin/dashboard/', denuncias_views.dashboard, name='admin_dashboard'),
    path('denuncias/admin/configuracion-metricas/reset-complaints/', denuncias_views.admin_reset_complaints, name='admin_reset_complaints'),
    path('denuncias/admin/verify/<int:user_id>/', denuncias_views.admin_verify, name='admin_verify'),
    path('admin/login/', RedirectView.as_view(pattern_name='denuncias:admin_login'), name='admin_login_root'),
    path('admin/dashboard/', RedirectView.as_view(pattern_name='denuncias:admin_dashboard'), name='admin_dashboard_root'),
    path('delegador/', RedirectView.as_view(pattern_name='denuncias:delegador_queue'), name='delegador_root'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
