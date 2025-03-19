from django.urls import path
from .views import *

urlpatterns = [
    # Набор методов для услуг
    path('api/devices/', search_devices),  # GET
    path('api/devices/<int:device_id>/', get_device_by_id),  # GET
    path('api/devices/<int:device_id>/update/', update_device),  # PUT
    path('api/devices/<int:device_id>/update_image/', update_device_image),  # POST
    path('api/devices/<int:device_id>/delete/', delete_device),  # DELETE
    path('api/devices/create/', create_device),  # POST
    path('api/devices/<int:device_id>/add_to_service/', add_device_to_service),  # POST

    # Набор методов для заявок
    path('api/services/', search_services),  # GET
    path('api/services/<int:service_id>/', get_service_by_id),  # GET
    path('api/services/<int:service_id>/update/', update_service),  # PUT
    path('api/services/<int:service_id>/update_status_user/', update_status_user),  # PUT
    path('api/services/<int:service_id>/update_status_admin/', update_status_admin),  # PUT
    path('api/services/<int:service_id>/delete/', delete_service),  # DELETE

    # Набор методов для м-м
    path('api/services/<int:service_id>/update_device/<int:device_id>/', update_device_in_service),  # PUT
    path('api/services/<int:service_id>/delete_device/<int:device_id>/', delete_device_from_service),  # DELETE

    # Набор методов для аутентификации и авторизации
    path("api/users/register/", register),  # POST
    path("api/users/login/", login),  # POST
    path("api/users/logout/", logout),  # POST
    path("api/users/<int:user_id>/update/", update_user)  # PUT
]
