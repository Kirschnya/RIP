from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('devices/<int:device_id>/', device_details, name="device_details"),
    path('devices/<int:device_id>/add_to_service/', add_device_to_draft_service, name="add_device_to_draft_service"),
    path('services/<int:service_id>/delete/', delete_service, name="delete_service"),
    path('services/<int:service_id>/', service)
]
