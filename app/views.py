from django.contrib.auth.models import User
from django.db import connection
from django.shortcuts import render, redirect
from django.utils import timezone

from app.models import Devices, Service, DevicesService


def index(request):
    device_name = request.GET.get("device_name", "")
    devices = Devices.objects.filter(status=1)

    if device_name:
        devices = devices.filter(name__icontains=device_name)

    draft_service = get_draft_service()

    context = {
        "device_name": device_name,
        "devices": devices
    }

    if draft_service:
        context["devices_count"] = len(draft_service.get_devices())
        context["draft_service"] = draft_service

    return render(request, "devices_page.html", context)


def add_device_to_draft_service(request, device_id):
    device_name = request.POST.get("device_name")
    redirect_url = f"/?device_name={device_name}" if device_name else "/"

    device = Devices.objects.get(pk=device_id)

    draft_service = get_draft_service()

    if draft_service is None:
        draft_service = Service.objects.create()
        draft_service.owner = get_current_user()
        draft_service.date_created = timezone.now()
        draft_service.save()

    if DevicesService.objects.filter(service=draft_service, device=device).exists():
        return redirect(redirect_url)

    item = DevicesService(
        service=draft_service,
        device=device
    )
    item.save()

    return redirect(redirect_url)


def device_details(request, device_id):
    context = {
        "device": Devices.objects.get(id=device_id)
    }

    return render(request, "device_page.html", context)


def delete_service(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return redirect("/")

    with connection.cursor() as cursor:
        cursor.execute("UPDATE services SET status=5 WHERE id = %s", [service_id])

    return redirect("/")


def service(request, service_id):
    if not Service.objects.filter(pk=service_id).exists():
        return redirect("/")

    service = Service.objects.get(id=service_id)
    if service.status == 5:
        return redirect("/")

    context = {
        "service": service,
    }

    return render(request, "service_page.html", context)


def get_draft_service():
    return Service.objects.filter(status=1).first()


def get_current_user():
    return User.objects.filter(is_superuser=False).first()