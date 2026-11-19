from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('', views.api_root, name='root'),
    path('complaints/', views.complaint_create, name='complaint-create'),
    path('complaints/lookup/', views.complaint_lookup, name='complaint-lookup'),
    path('complaints/chat/', views.complaint_chat, name='complaint-chat'),
    path('complaints/notes/', views.complaint_notes, name='complaint-notes'),
    path('complaints/attachments/', views.complaint_attachments, name='complaint-attachments'),
    path('complaints/attachments/<str:token>/download/', views.complaint_attachment_download,
         name='complaint-attachment-download'),
    path('privacy-notices/', views.privacy_notices, name='privacy-notices'),
]
