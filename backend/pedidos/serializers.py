# pedidos/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.dateparse import parse_datetime
from django.utils import timezone  # ← NECESARIO para validate_due_at

from .models import (
    Pedido,
    PedidoCrucero,
    Empresa,
    CustomUser,
    Reminder,
)

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
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion", "updates"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user
        validated_data["empresa"] = (
            request.user.empresa
        )  # si CustomUser.empresa fuese FK, ajusta a request.user.empresa_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Si no tienes servicios en el modelo, elimina estas dos líneas
        servicios_data = validated_data.pop("servicios", None)
        instance = super().update(instance, validated_data)
        if servicios_data is not None and hasattr(instance, "servicios"):
            instance.servicios.all().delete()
        return instance


class DateOrDateTimeToDateField(serializers.DateField):
    def to_internal_value(self, value):
        if isinstance(value, str) and "T" in value:
            value = value.split("T", 1)[0]  # quedarse con YYYY-MM-DD
        return super().to_internal_value(value)


# ====== OPS (Lectura) ======
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ["id", "nombre"]


class PedidoOpsSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(
        queryset=Empresa.objects.all(),
        required=False,
        allow_null=True,
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Pedido
        fields = [
            "id",
            "user",
            "empresa",
            "excursion",
            "fecha_inicio",
            "fecha_fin",
            "tipo_servicio",
            "estado",
            "lugar_entrega",
            "lugar_recogida",
            "notas",
            "bono",
            "emisores",
            "pax",
            "guia",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "No autenticado."})

        if user.is_staff:
            if not attrs.get("empresa"):
                raise serializers.ValidationError(
                    {"empresa": "Este campo es obligatorio para staff."}
                )
            return attrs

        # No-staff: resolver Empresa por nombre (CustomUser.empresa es CharField)
        nombre = (getattr(user, "empresa", "") or "").strip()
        if not nombre:
            raise serializers.ValidationError(
                {"empresa": "Tu usuario no tiene empresa asignada."}
            )

        try:
            empresa_obj = Empresa.objects.get(nombre=nombre)
        except Empresa.DoesNotExist:
            raise serializers.ValidationError(
                {"empresa": f"No existe Empresa con nombre '{nombre}' asociada a tu usuario."}
            )

        attrs["empresa"] = empresa_obj
        return attrs


# ====== OPS (Escritura) ======
class PedidoOpsWriteSerializer(serializers.ModelSerializer):
    fecha_inicio = DateOrDateTimeToDateField(required=True)
    fecha_fin = DateOrDateTimeToDateField(required=False, allow_null=True)
    tipo_servicio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emisores = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")

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
            "emisores",
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
        if not attrs.get("emisores"):
            attrs["emisores"] = ""
        return attrs


class PedidoCruceroSerializer(serializers.ModelSerializer):
    printing_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PedidoCrucero
        fields = "__all__"
        read_only_fields = ["uploaded_at", "updated_at"]
        extra_kwargs = {
            "emergency_contact": {"required": False, "allow_blank": True},
            "language": {"required": False, "allow_blank": True},
            "arrival_time": {"required": False, "allow_null": True},
        }

    def create(self, validated):
        key = {
            "service_date": validated["service_date"],
            "ship": validated["ship"],
            "sign": validated["sign"],
        }
        nuevo_status = validated["status"]

        existente = PedidoCrucero.objects.filter(**key).first()
        if existente:
            if existente.status == "final" and nuevo_status == "preliminary":
                raise serializers.ValidationError(
                    "Registro final ya confirmado; no se puede reemplazar por preliminary."
                )
            for campo, valor in validated.items():
                setattr(existente, campo, valor)
            existente.save()
            self.instance = existente
            return existente

        return PedidoCrucero.objects.create(**validated)

    def validate(self, attrs):
        if not attrs.get("service_date") or not attrs.get("ship"):
            raise serializers.ValidationError("service_date y ship son obligatorios.")
        return attrs


# ====== Reminders ======
class ReminderSerializer(serializers.ModelSerializer):
    """
    Acepta payloads con:
      - title
      - notes  -> mapeado al campo real existente (note/description/...)
      - due_at -> mapeado al campo real existente (when/at/...)
    Inyecta 'user' si el modelo tiene ese FK.
    """

    class Meta:
        model = Reminder
        fields = "__all__"
        read_only_fields = []

    # Aliases aceptados desde el frontend
    NOTES_ALIASES = ["notes", "note", "notas", "nota", "description", "details",
                     "observaciones", "body", "text", "mensaje", "content"]
    DUE_ALIASES   = ["due_at", "when", "scheduled_at", "scheduled_for",
                     "remind_at", "at", "fecha", "fecha_hora"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos concretos del modelo
        self._fields_in_model = {
            f.name for f in self.Meta.model._meta.get_fields()
            if getattr(f, "concrete", False)
            and not getattr(f, "many_to_many", False)
            and not getattr(f, "auto_created", False)
        }

        # Resolver nombre real de campos "notes" y "due_at" en el modelo
        self.real_notes_field = next((n for n in self.NOTES_ALIASES if n in self._fields_in_model), None)
        self.real_due_field   = next((n for n in self.DUE_ALIASES   if n in self._fields_in_model), None)

        # Si el modelo tiene FK user, lo ocultamos e inyectamos CurrentUser
        if "user" in self._fields_in_model:
            self.fields["user"] = serializers.HiddenField(default=serializers.CurrentUserDefault())

        # Marcar algunos como solo-lectura si existen
        for ro in ("id", "created_at", "done_at"):
            if ro in self.fields:
                self.fields[ro].read_only = True

    def to_internal_value(self, data):
        """
        Mapea alias del payload a los nombres reales del modelo.
        Normaliza fecha/hora y la vuelve aware.
        """
        if not isinstance(data, dict):
            return super().to_internal_value(data)

        data = dict(data)  # copia

        # Mapear notes -> campo real
        if "notes" in data and self.real_notes_field and self.real_notes_field != "notes":
            data[self.real_notes_field] = data.pop("notes")

        # Mapear due_at -> campo real
        if "due_at" in data and self.real_due_field and self.real_due_field != "due_at":
            data[self.real_due_field] = data.pop("due_at")

        # Normalizar fecha si la tenemos
        if self.real_due_field and self.real_due_field in data:
            raw = data[self.real_due_field]
            dt = None
            if isinstance(raw, str):
                # admite 'Z' al final
                raw2 = raw.replace("Z", "+00:00")
                dt = parse_datetime(raw2)
            elif isinstance(raw, timezone.datetime):
                dt = raw

            if dt is None:
                raise serializers.ValidationError({self.real_due_field: "Formato de fecha inválido."})

            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())

            data[self.real_due_field] = dt

        return super().to_internal_value(data)

    def validate(self, attrs):
        # Si hay fecha, que no sea pasada
        if self.real_due_field and self.real_due_field in attrs:
            dt = attrs[self.real_due_field]
            if dt < timezone.now():
                raise serializers.ValidationError({self.real_due_field: "No puede ser en el pasado."})
        return attrs

    def create(self, validated_data):
        # Inyectar user si existe en el modelo y no vino (HiddenField suele cubrirlo)
        if "user" in self._fields_in_model and "user" not in validated_data:
            req = self.context.get("request")
            if req and getattr(req, "user", None) and req.user.is_authenticated:
                validated_data["user"] = req.user
        return super().create(validated_data)
