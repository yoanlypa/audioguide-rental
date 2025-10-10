# pedidos/serializers.py
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Pedido, PedidoCrucero, Empresa, CustomUser, Reminder

User = get_user_model()


# -----------------------------
#  Auth
# -----------------------------
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

        if not (email and password):
            raise serializers.ValidationError({"detail": "Debe incluir email y contraseña."})

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )
        if not user:
            raise serializers.ValidationError({"detail": "Credenciales inválidas."})

        refresh = self.get_token(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


# -----------------------------
#  Helpers
# -----------------------------
class DateOrDateTimeToDateField(serializers.DateField):
    """
    Permite strings ISO con hora (YYYY-MM-DDTHH:MM...) y conserva sólo la fecha.
    """
    def to_internal_value(self, value):
        if isinstance(value, str) and "T" in value:
            value = value.split("T", 1)[0]
        return super().to_internal_value(value)


# -----------------------------
#  Empresas
# -----------------------------
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ["id", "nombre"]


# -----------------------------
#  Pedido "genérico" (usado en /api/pedidos/ y mis-pedidos)
#  OJO: Corrección para empresa FK si se usa este serializer.
# -----------------------------
class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion", "updates"]

    def create(self, validated_data):
        """
        - user siempre es el request.user
        - empresa:
            * Si viene en el payload (p.ej. staff), se respeta.
            * Si NO viene y el usuario NO es staff, se resuelve por nombre (CustomUser.empresa).
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "No autenticado."})

        validated_data["user"] = user

        if not validated_data.get("empresa"):
            if user.is_staff:
                raise serializers.ValidationError({"empresa": "Empresa es obligatoria para staff."})
            nombre = (getattr(user, "empresa", "") or "").strip()
            if not nombre:
                raise serializers.ValidationError({"empresa": "Tu usuario no tiene empresa asignada."})
            try:
                empresa_obj = Empresa.objects.get(nombre=nombre)
            except Empresa.DoesNotExist:
                raise serializers.ValidationError({"empresa": f"No existe Empresa con nombre '{nombre}' asociada a tu usuario."})
            validated_data["empresa"] = empresa_obj

        # Limpieza básica de strings
        for k in ["excursion", "lugar_entrega", "lugar_recogida", "notas", "bono", "guia", "tipo_servicio", "estado"]:
            if k in validated_data and isinstance(validated_data[k], str):
                validated_data[k] = validated_data[k].strip()

        return super().create(validated_data)

    # (Tu método update previo referenciaba "servicios" y rompía. Lo retiramos.)


# -----------------------------
#  Pedidos – Lectura (OPS board)
# -----------------------------
class PedidoOpsSerializer(serializers.ModelSerializer):
    # Si el usuario no es staff, empresa la inyectamos en el View/WriteSerializer
    empresa = serializers.PrimaryKeyRelatedField(
        queryset=Empresa.objects.all(),
        required=False,
        allow_null=True
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
        """
        Validación ligera para lecturas/escrituras mínimas desde el board.
        (La creación robusta la hacemos con PedidoOpsWriteSerializer.)
        """
        return attrs


# -----------------------------
#  Pedidos – Escritura (OPS board → crear pedido)
# -----------------------------
class PedidoOpsWriteSerializer(serializers.ModelSerializer):
    fecha_inicio = DateOrDateTimeToDateField(required=True)
    fecha_fin = DateOrDateTimeToDateField(required=False, allow_null=True)
    tipo_servicio = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # emisores en el modelo es PositiveIntegerField(null=True, blank=True)
    # Aceptamos "", null o número.
    emisores = serializers.IntegerField(required=False, allow_null=True)

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

        # Normaliza tipo_servicio tal como lo requiere tu modelo (sin romper lo existente)
        ts = attrs.get("tipo_servicio")
        if ts:
            ts = ts.strip()
            # Permite valores “frontend friendly” y los traduce si hace falta:
            alias = {
                "mediodia": "mediodia",
                "medio_dia": "mediodia",
                "medio-dia": "mediodia",
                "dia_completo": "dia_Completo",
                "día completo": "dia_Completo",
                "dia completo": "dia_Completo",
                "circuito": "circuito",
                "crucero": "crucero",
            }
            attrs["tipo_servicio"] = alias.get(ts, ts)

        # emisores: si vino vacío como string → None
        if "emisores" in attrs and attrs["emisores"] == "":
            attrs["emisores"] = None

        # Limpieza básica
        for k in ["excursion", "lugar_entrega", "lugar_recogida", "notas", "bono", "guia", "estado"]:
            if k in attrs and isinstance(attrs[k], str):
                attrs[k] = attrs[k].strip()

        return attrs


# -----------------------------
#  Cruceros
# -----------------------------
class PedidoCruceroSerializer(serializers.ModelSerializer):
    # printing_date lo fija el backend (read_only)
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
            "ship":        validated["ship"],
            "sign":        validated["sign"],
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
class ReminderSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Reminder
        fields = ["id", "user", "title", "note", "due_at", "created_at", "done"]
        read_only_fields = ["id", "created_at"]

    def validate_due_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("La fecha/hora debe ser futura.")
        return value