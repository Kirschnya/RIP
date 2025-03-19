from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User


class Devices(models.Model):
    STATUS_CHOICES = (
        (1, 'Действует'),
        (2, 'Удалена'),
    )

    name = models.CharField(max_length=100, verbose_name="Название", blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    image = models.ImageField(default="default.png", blank=True)
    description = models.TextField(verbose_name="Описание", blank=True)

    cables = models.IntegerField(blank=True)

    def get_image(self):
        return self.image.url.replace("minio", "localhost", 1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        db_table = "devices"


class Service(models.Model):
    STATUS_CHOICES = (
        (1, 'Введён'),
        (2, 'В работе'),
        (3, 'Завершен'),
        (4, 'Отклонен'),
        (5, 'Удален')
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(default=timezone.now(), verbose_name="Дата создания")
    date_formation = models.DateTimeField(verbose_name="Дата формирования", blank=True, null=True)
    date_complete = models.DateTimeField(verbose_name="Дата завершения", blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Пользователь", null=True, related_name='owner')
    moderator = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Сотрудник", null=True, related_name='moderator')

    description = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return "заказ №" + str(self.pk)

    def get_devices(self):
        return [
            setattr(item.device, "comment", item.comment) or item.device
            for item in DevicesService.objects.filter(service=self)
        ]

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ('-date_formation',)
        db_table = "services"


class DevicesService(models.Model):
    device = models.ForeignKey(Devices, models.DO_NOTHING, blank=True, null=True)
    service = models.ForeignKey(Service, models.DO_NOTHING, blank=True, null=True)
    comment = models.CharField(blank=True, null=True)

    def __str__(self):
        return "м-м №" + str(self.pk)

    class Meta:
        verbose_name = "м-м"
        verbose_name_plural = "м-м"
        db_table = "device_service"
        unique_together = ('device', 'service')
