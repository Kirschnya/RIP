import os

from rest_framework import serializers

from .models import *


class DevicesSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, device):
        if device.image:
            return device.image.url.replace("minio", os.getenv("IP_ADDRESS"), 1)

        return f"http://{os.getenv("IP_ADDRESS")}:9000/images/default.png"

    class Meta:
        model = Device
        fields = ("id", "name", "status", "cables", "image")


class DeviceSerializer(DevicesSerializer):
    class Meta(DevicesSerializer.Meta):
        fields = "__all__"


class ServicesSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    moderator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Service
        fields = "__all__"


class ServiceSerializer(ServicesSerializer):
    devices = serializers.SerializerMethodField()
            
    def get_devices(self, service):
        items = service.deviceservice_set.all()
        return [DeviceItemSerializer(item.device, context={"comment": item.comment}).data for item in items]


class DeviceItemSerializer(DeviceSerializer):
    comment = serializers.SerializerMethodField()

    def get_comment(self, _):
        return self.context.get("comment")

    class Meta:
        model = Device
        fields = ("id", "name", "status", "cables", "image", "comment")


class DeviceServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceService
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', "is_superuser")


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
