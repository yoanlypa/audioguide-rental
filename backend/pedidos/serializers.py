from rest_framework import serializers
from .models import Pedido, PedidoCrucero
from .models import CustomUser
from django.contrib.auth import authenticate, get_user_model
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import PedidoCrucero

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "empresa"]


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), email=email, password=password
            )

            if not user:
                raise serializers.ValidationError(
                    ("Credenciales inválidas."), code="authorization"
                )
        else:
            raise serializers.ValidationError(
                ("Debe incluir email y contraseña."), code="authorization"
            )

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class PedidoSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)

    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = ["user", "empresa", "fecha_creacion", "updates"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user
        validated_data["empresa"] = (
            request.user.empresa
        )  # asumiendo que User tiene un campo empresa
        return super().create(validated_data)

    def update(self, instance, validated_data):
        servicios_data = validated_data.pop("servicios")
        instance = super().update(instance, validated_data)

        # Elimina servicios existentes
        instance.servicios.all().delete()

class PedidoCruceroSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PedidoCrucero
        fields = "__all__"
        extra_kwargs = {
            # ❌ No exigir emergency_contact
            "emergency_contact": {"required": False, "allow_blank": True},
            # ✉️ Otros campos opcionales
            "language":   {"required": False, "allow_blank": True},
            "arrival_time": {"required": False, "allow_null": True},
        }
    def create(self, validated):
        key = {
            "service_date": validated["service_date"],
            "ship":        validated["ship"],
            "sign":        validated["sign"],
        }
        nuevo_status = validated["status"]

        existente = PedidoCrucero.objects.filter(**key).first()

        if existente:
            # 1️⃣  Si el existente es FINAL y llega PRELIMINARY → error
            if existente.status == "final" and nuevo_status == "preliminary":
                raise serializers.ValidationError(
                    "Registro final ya confirmado; no se puede reemplazar por preliminary."
                )
            # 2️⃣  En cualquier otro caso, sobreescribimos
            for campo, valor in validated.items():
                setattr(existente, campo, valor)
            existente.save()
            self.instance = existente
            return existente

        # 3️⃣  No existe → creamos normalmente
        return PedidoCrucero.objects.create(**validated)


    def validate(self, attrs):
        if not attrs.get("service_date") or not attrs.get("ship"):
            raise serializers.ValidationError(
                "service_date y ship son obligatorios."
            )
        return attrs