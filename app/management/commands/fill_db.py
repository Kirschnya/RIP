import random

from django.core.management.base import BaseCommand
from minio import Minio

from ...models import *
from .utils import random_date, random_timedelta


def add_users():
    User.objects.create_user("user", "user@user.com", "1234", first_name="user", last_name="user")
    User.objects.create_superuser("root", "root@root.com", "1234", first_name="root", last_name="root")

    for i in range(1, 10):
        User.objects.create_user(f"user{i}", f"user{i}@user.com", "1234", first_name=f"user{i}", last_name=f"user{i}")
        User.objects.create_superuser(f"root{i}", f"root{i}@root.com", "1234", first_name=f"user{i}", last_name=f"user{i}")

    print("Пользователи созданы")


def add_devices():
    Devices.objects.create(
        name="Проектор ACER",
        description="Позволяет выводить изображение с ноутубка",
        cables=3,
        image="6.png"
    )

    Devices.objects.create(
        name="Микрофон СОЮЗ",
        description="Захватывает звук лектора. Для самых шумных аудиторий.",
        cables=2,
        image="2.png",
    )

    Devices.objects.create(
        name="Микрофон SVEN5",
        description="Простой и удобный в использовании. Портативный.",
        cables=1,
        image="1.png"
    )

    Devices.objects.create(
        name="Динамики SVEN MK200",
        description="Позволяют выводить звук с ноутбука",
        cables=2,
        image="3.png",

    )

    Devices.objects.create(
        name="Ноутубк",
        description="Мощный и портативный. Предустановлена Alt Linux.",
        cables=1,
        image="5.png"
 
    )

    Devices.objects.create(
        name="Проектор BENQ",
        description="Работает без провода, благодаря технологии Wi-Fi Direct.",
        cables=1,
        image="4.png"
    )

    client = Minio("minio:9000", "minio", "minio123", secure=False)
    client.fput_object('images', '1.png', "app/static/images/1.png")
    client.fput_object('images', '2.png', "app/static/images/2.png")
    client.fput_object('images', '3.png', "app/static/images/3.png")
    client.fput_object('images', '4.png', "app/static/images/4.png")
    client.fput_object('images', '5.png', "app/static/images/5.png")
    client.fput_object('images', '6.png', "app/static/images/6.png")
    client.fput_object('images', 'default.png', "app/static/images/default.png")

    print("Услуги добавлены")


def add_services():
    users = User.objects.filter(is_superuser=False)
    moderators = User.objects.filter(is_superuser=True)

    if len(users) == 0 or len(moderators) == 0:
        print("Заявки не могут быть добавлены. Сначала добавьте пользователей с помощью команды add_users")
        return

    devices = Devices.objects.all()

    for _ in range(30):
        status = random.randint(2, 5)
        add_service(status, devices, users, moderators)

    add_service(1, devices, users, moderators)

    print("Заявки добавлены")


def add_service(status, devices, users, moderators):
    service = Service.objects.create()
    service.status = status

    if service.status in [3, 4]:
        service.date_complete = random_date()
        service.date_formation = service.date_complete - random_timedelta()
        service.date_created = service.date_formation - random_timedelta()
    else:
        service.date_formation = random_date()
        service.date_created = service.date_formation - random_timedelta()

    service.owner = random.choice(users)
    service.moderator = random.choice(moderators)

    service.description = "Описание заказа"
    service.date = random_date()

    for device in random.sample(list(devices), 3):
        item = DevicesService(
            service=service,
            device=device,
            comment="Развернутый комментарий"
        )
        item.save()

    service.save()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        add_users()
        add_devices()
        add_services()



















