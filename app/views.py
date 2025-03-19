from datetime import timedelta
import uuid

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .permissions import *
from .redis import session_storage
from .serializers import *
from .utils import identity_user, get_session, random_date


def get_draft_service(request):
    user = identity_user(request)

    if user is None:
        return None

    service = Service.objects.filter(owner=user).filter(status=1).first()

    return service


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'device_name',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
def search_devices(request):
    device_name = request.GET.get("device_name", "")

    devices = Device.objects.filter(status=1)

    if device_name:
        devices = devices.filter(name__icontains=device_name)

    serializer = DevicesSerializer(devices, many=True)

    draft_service = get_draft_service(request)

    resp = {
        "devices": serializer.data,
        "devices_count": DeviceService.objects.filter(service=draft_service).count() if draft_service else None,
        "draft_service_id": draft_service.pk if draft_service else None
    }

    return Response(resp)


@api_view(["GET"])
def get_device_by_id(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)
    serializer = DeviceSerializer(device)

    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=DeviceSerializer)
@api_view(["PUT"])
@permission_classes([IsModerator])
def update_device(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)

    serializer = DeviceSerializer(device, data=request.data)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(method='POST', request_body=DeviceAddSerializer)
@api_view(["POST"])
@permission_classes([IsModerator])
@parser_classes((MultiPartParser,))
def create_device(request):
    serializer = DeviceAddSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    Device.objects.create(**serializer.validated_data)

    devices = Device.objects.filter(status=1)
    serializer = DevicesSerializer(devices, many=True)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsModerator])
def delete_device(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)
    device.status = 2
    device.save()

    device = Device.objects.filter(status=1)
    serializer = DeviceSerializer(device, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_device_to_service(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)

    draft_service = get_draft_service(request)

    if draft_service is None:
        draft_service = Service.objects.create()
        draft_service.date_created = timezone.now()
        draft_service.owner = identity_user(request)
        draft_service.save()

    if DeviceService.objects.filter(service=draft_service, device=device).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = DeviceService.objects.create()
    item.service = draft_service
    item.device = device
    item.save()

    serializer = ServiceSerializer(draft_service)
    return Response(serializer.data["devices"])


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE),
    ]
)
@api_view(["POST"])
@permission_classes([IsModerator])
@parser_classes((MultiPartParser,))
def update_device_image(request, device_id):
    if not Device.objects.filter(pk=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    device = Device.objects.get(pk=device_id)

    image = request.data.get("image")

    if image is None:
        return Response(status.HTTP_400_BAD_REQUEST)

    device.image = image
    device.save()

    serializer = DeviceSerializer(device)

    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'date_formation_start',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date_formation_end',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_services(request):
    status_id = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    services = Service.objects.exclude(status__in=[1, 5])

    user = identity_user(request)
    if not user.is_superuser:
        services = services.filter(owner=user)

    if status_id > 0:
        services = services.filter(status=status_id)

    if date_formation_start and parse_datetime(date_formation_start):
        services = services.filter(date_formation__gt=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        services = services.filter(date_formation__lt=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = ServicesSerializer(services, many=True)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_service_by_id(request, service_id):
    user = identity_user(request)

    if not Service.objects.filter(pk=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)

    if not user.is_superuser and service.owner != user:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ServiceSerializer(service)

    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=ServiceSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_service(request, service_id):
    user = identity_user(request)

    if not Service.objects.filter(pk=service_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)
    serializer = ServiceSerializer(service, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_status_user(request, service_id):
    user = identity_user(request)

    if not Service.objects.filter(pk=service_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)

    if service.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    service.status = 2
    service.date_formation = timezone.now()
    service.save()

    serializer = ServiceSerializer(service)

    return Response(serializer.data)


@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    )
)
@api_view(["PUT"])
@permission_classes([IsModerator])
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

    service.status = request_status
    service.date_complete = timezone.now()
    service.moderator = identity_user(request)
    service.save()

    serializer = ServiceSerializer(service)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_service(request, service_id):
    user = identity_user(request)

    if not Service.objects.filter(pk=service_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    service = Service.objects.get(pk=service_id)

    if service.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    service.status = 5
    service.save()

    return Response(status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_device_from_service(request, service_id, device_id):
    user = identity_user(request)

    if not Service.objects.filter(pk=service_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not DeviceService.objects.filter(service_id=service_id, device_id=device_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = DeviceService.objects.get(service_id=service_id, device_id=device_id)
    item.delete()

    service = Service.objects.get(pk=service_id)

    serializer = ServiceSerializer(service)
    devices = serializer.data["devices"]

    return Response(devices)


@swagger_auto_schema(method='PUT', request_body=DeviceServiceSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_device_in_service(request, service_id, device_id):
    user = identity_user(request)

    if not Service.objects.filter(pk=service_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not DeviceService.objects.filter(device_id=device_id, service_id=service_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = DeviceService.objects.get(device_id=device_id, service_id=service_id)

    serializer = DeviceServiceSerializer(item, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_200_OK)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@swagger_auto_schema(method='post', request_body=UserRegisterSerializer)
@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_201_CREATED)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    session = get_session(request)
    session_storage.delete(session)

    response = Response(status=status.HTTP_200_OK)
    response.delete_cookie('session_id')

    return response


@swagger_auto_schema(method='PUT', request_body=UserProfileSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = identity_user(request)

    if user.pk != user_id:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    password = request.data.get("password", None)
    if password is not None and not user.check_password(password):
        user.set_password(password)
        user.save()

    return Response(serializer.data, status=status.HTTP_200_OK)
