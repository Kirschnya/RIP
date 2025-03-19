import random
from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .management.commands.utils import random_date
from .serializers import *


def get_draft_service():
    return Service.objects.filter(status=1).first()


def get_user():
    return User.objects.filter(is_superuser=False).first()


def get_moderator():
    return User.objects.filter(is_superuser=True).first()


@api_view(["GET"])
def search_devices(request):
    device_name = request.GET.get("device_name", "")

    devices = Device.objects.filter(status=1)

    if device_name:
        devices = devices.filter(name__icontains=device_name)

    serializer = DevicesSerializer(devices, many=True)
    
    draft_service = get_draft_service()

    resp = {
        "devices": serializer.data,
        "devices_count": DeviceService.objects.filter(service=draft_service).count() if draft_service else None,
        "draft_service": draft_service.pk if draft_service else None
    }

    return Response(resp)


@api_view(["GET"])
def get_device_by_id(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)
    serializer = DeviceSerializer(device)

    return Response(serializer.data)


@api_view(["PUT"])
def update_device(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)

    serializer = DeviceSerializer(device, data=request.data, partial=True)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def create_device(request):
    serializer = DeviceSerializer(data=request.data, partial=False)

    serializer.is_valid(raise_exception=True)

    Device.objects.create(**serializer.validated_data)

    devices = Device.objects.filter(status=1)
    serializer = DeviceSerializer(devices, many=True)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_device(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)
    device.status = 2
    device.save()

    devices = Device.objects.filter(status=1)
    serializer = DeviceSerializer(devices, many=True)

    return Response(serializer.data)


@api_view(["POST"])
def add_device_to_service(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)

    draft_service = get_draft_service()

    if draft_service is None:
        draft_service = Service.objects.create()
        draft_service.owner = get_user()
        draft_service.date_created = timezone.now()
        draft_service.save()

    if DeviceService.objects.filter(service=draft_service, device=device).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    item = DeviceService.objects.create()
    item.service = draft_service
    item.device = device
    item.save()

    serializer = ServiceSerializer(draft_service)
    return Response(serializer.data["devices"])


@api_view(["POST"])
def update_device_image(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)

    image = request.data.get("image")
    if image is not None:
        device.image = image
        device.save()

    serializer = DeviceSerializer(device)

    return Response(serializer.data)


@api_view(["GET"])
def search_services(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    services = Service.objects.exclude(status__in=[1, 5])

    if status > 0:
        services = services.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        services = services.filter(date_formation__gt=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        services = services.filter(date_formation__lt=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = ServicesSerializer(services, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_service_by_id(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)

    print(service.deviceservice_set.all())

    serializer = ServiceSerializer(service, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_service(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)
    serializer = ServiceSerializer(service, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_user(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)

    if service.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    service.status = 2
    service.date_formation = timezone.now()
    service.save()

    serializer = ServiceSerializer(service, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_admin(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])

    if request_status not in [3, 4]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    service = Service.objects.get(pk=service_id)

    if service.status != 2:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if request_status == 3:
        service.date = random_date()

    service.date_complete = timezone.now()
    service.status = request_status
    service.moderator = get_moderator()
    service.save()

    return Response(status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_service(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)

    if service.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    service.status = 5
    service.save()

    serializer = ServiceSerializer(service, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_device_from_service(request, service_id, device_id):
    if not DeviceService.objects.filter(service_id=service_id, device_id=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = DeviceService.objects.get(service_id=service_id, device_id=device_id)
    item.delete()

    items = DeviceService.objects.filter(service_id=service_id)
    data = [DeviceItemSerializer(item.device, context={"comment": item.comment}).data for item in items]

    return Response(data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_device_in_service(request, service_id, device_id):
    if not DeviceService.objects.filter(device_id=device_id, service_id=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = DeviceService.objects.get(device_id=device_id, service_id=service_id)

    serializer = DeviceServiceSerializer(item, data=request.data,  partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def logout(request):
    return Response(status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_user(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = User.objects.get(pk=user_id)
    serializer = UserSerializer(user, data=request.data, partial=True)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data)