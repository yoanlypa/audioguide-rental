from rest_framework import serializers
from .models import Pedido, PedidoCrucero
from .models import CustomUser
from django.contrib.auth import authenticate, get_user_model
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import PedidoCrucero, Empresa
from django.contrib.auth import get_user_model

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
    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion", "updates"]
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


class DateOrDateTimeToDateField(serializers.DateField):
    def to_internal_value(self, value):
        if isinstance(value, str) and "T" in value:
            value = value.split("T", 1)[0]  # nos quedamos con la parte de fecha
        return super().to_internal_value(value)

# ===== LECTURA (board) =====
class PedidoOpsSerializer(serializers.ModelSerializer):
    empresa = serializers.SerializerMethodField()
    entregado = serializers.SerializerMethodField()
    recogido = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = (
            "id",
            "empresa",
            "excursion",
            "estado",
            "lugar_entrega",
            "lugar_recogida",
            "fecha_inicio",
            "fecha_fin",
            "pax",
            "bono",
            "guia",
            "tipo_servicio",
            "emisores",          # <-- NUEVO
            "notas",
            "updates",
            "fecha_creacion",
            # "fecha_modificacion",
            "entregado",
            "recogido",
        )
        read_only_fields = ("id", "updates", "fecha_creacion", "entregado", "recogido")

    def get_empresa(self, obj):
        val = getattr(obj, "empresa", None)
        return str(val) if val is not None else ""

    def get_entregado(self, obj):
        return (getattr(obj, "estado", "") or "").lower() == "entregado"

    def get_recogido(self, obj):
        return (getattr(obj, "estado", "") or "").lower() == "recogido"


# --- ESCRITURA ---
class PedidoOpsWriteSerializer(serializers.ModelSerializer):
    # fechas flexibles ya como lo tenías
    fecha_inicio = DateOrDateTimeToDateField(required=True)
    fecha_fin = DateOrDateTimeToDateField(required=False, allow_null=True)
    tipo_servicio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emisores = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")  # <-- NUEVO

    class Meta:
        model = Pedido
        fields = (
            "empresa",
            "excursion",
            "estado",
            "lugar_entrega",
            "lugar_recogida",
            "fecha_inicio",
            "fecha_fin",
            "pax",
            "bono",
            "guia",
            "tipo_servicio",
            "emisores",          # <-- NUEVO
            "notas",
        )
        extra_kwargs = {
            "empresa": {"required": True},
            "fecha_inicio": {"required": True},
            "fecha_fin": {"required": False, "allow_null": True},
            "estado": {"required": False},
            "pax": {"required": False},
        }

    def validate(self, attrs):
        fi = attrs.get("fecha_inicio")
        ff = attrs.get("fecha_fin")
        if ff and fi and ff < fi:
            raise serializers.ValidationError({"fecha_fin": "Debe ser >= fecha_inicio."})
        # default defensivo para NOT NULL
        if not attrs.get("emisores"):
            attrs["emisores"] = ""
        return attrs
    
class PedidoCruceroSerializer(serializers.ModelSerializer):
    printing_date = serializers.DateTimeField(read_only=True)
    class Meta:
        model  = PedidoCrucero
        fields = "__all__"
        read_only_fields = ["uploaded_at", "updated_at"]
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
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ["id", "nombre"]