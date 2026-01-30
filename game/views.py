from django.shortcuts import render
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from .models import Profile, WithdrawalRequest
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from decimal import Decimal
from django.utils import timezone


@ensure_csrf_cookie
def login_page(request):
    return render(request, "game/login.html")

def register_view(request):
    return render(request, "game/register.html")

@login_required
def home_view(request):
    return render(request, "game/home.html")

@require_POST
@csrf_protect
def login_view(request):
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({"error": "Credenciales inválidas"}, status=401)

        login(request, user)
        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    except Exception as e:
        print("LOGIN ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)
    
@require_POST
@csrf_protect
def register(request):
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password")
        password2 = data.get("password2")
        wallet = data.get("wallet", "").strip()

        if not all([username, email, password, password2, wallet]):
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        if password != password2:
            return JsonResponse({"error": "Las contraseñas no coinciden"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Usuario ya existe"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email ya registrado"}, status=400)

        if Profile.objects.filter(wallet_metamask_bsc=wallet).exists():
            return JsonResponse({"error": "Wallet ya registrada"}, status=400)

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            Profile.objects.create(
                user=user,
                wallet_metamask_bsc=wallet
            )

        return JsonResponse({"success": True}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    except Exception as e:
        print("REGISTER ERROR:", e)  # 🔴 SOLO PARA DEBUG
        return JsonResponse({"error": "Error interno"}, status=500)


@login_required
def profile_view(request):
    # Devuelve un fragmento HTML para insertar vía AJAX (modal)
    if request.method == "GET":
        return render(request, "game/profile.html", {"user": request.user, "profile": request.user.profile})
    return JsonResponse({"error": "Método no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
def profile_update(request):
    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        wallet = data.get("wallet", "").strip()

        if not all([username, email, wallet]):
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        user = request.user

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return JsonResponse({"error": "Usuario ya existe"}, status=400)

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return JsonResponse({"error": "Email ya registrado"}, status=400)

        if Profile.objects.filter(wallet_metamask_bsc=wallet).exclude(user=user).exists():
            return JsonResponse({"error": "Wallet ya registrada"}, status=400)

        with transaction.atomic():
            user.username = username
            user.email = email
            user.save()

            profile = user.profile
            profile.wallet_metamask_bsc = wallet
            profile.save()

        return JsonResponse({"success": True, "message": "Perfil actualizado"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        print("PROFILE UPDATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@ensure_csrf_cookie
def login_page(request):
    return render(request, "game/login.html")

def register_view(request):
    return render(request, "game/register.html")

@login_required
def home_view(request):
    return render(request, "game/home.html")

@require_POST
@csrf_protect
def login_view(request):
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({"error": "Credenciales inválidas"}, status=401)

        login(request, user)
        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    except Exception as e:
        print("LOGIN ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)
    
@require_POST
@csrf_protect
def register(request):
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password")
        password2 = data.get("password2")
        wallet = data.get("wallet", "").strip()

        if not all([username, email, password, password2, wallet]):
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        if password != password2:
            return JsonResponse({"error": "Las contraseñas no coinciden"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Usuario ya existe"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email ya registrado"}, status=400)

        if Profile.objects.filter(wallet_metamask_bsc=wallet).exists():
            return JsonResponse({"error": "Wallet ya registrada"}, status=400)

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            Profile.objects.create(
                user=user,
                wallet_metamask_bsc=wallet
            )

        return JsonResponse({"success": True}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    except Exception as e:
        print("REGISTER ERROR:", e)  # 🔴 SOLO PARA DEBUG
        return JsonResponse({"error": "Error interno"}, status=500)


@login_required
def profile_view(request):
    # Devuelve un fragmento HTML para insertar vía AJAX (modal)
    if request.method == "GET":
        return render(request, "game/profile.html", {"user": request.user, "profile": request.user.profile})
    return JsonResponse({"error": "Método no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
def profile_update(request):
    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        wallet = data.get("wallet", "").strip()

        if not all([username, email, wallet]):
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        user = request.user

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return JsonResponse({"error": "Usuario ya existe"}, status=400)

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return JsonResponse({"error": "Email ya registrado"}, status=400)

        if Profile.objects.filter(wallet_metamask_bsc=wallet).exclude(user=user).exists():
            return JsonResponse({"error": "Wallet ya registrada"}, status=400)

        with transaction.atomic():
            user.username = username
            user.email = email
            user.save()

            profile = user.profile
            profile.wallet_metamask_bsc = wallet
            profile.save()

        return JsonResponse({"success": True, "message": "Perfil actualizado"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        print("PROFILE UPDATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@login_required
def profile_view(request):
    # Devuelve la página de perfil (última definición - overrides previas)
    if request.method == "GET":
        profile, _ = Profile.objects.get_or_create(user=request.user)
        withdrawals = request.user.withdrawals.order_by('-created_at')
        return render(request, "game/profile.html", {"user": request.user, "profile": profile, "withdrawals": withdrawals})
    return JsonResponse({"error": "Método no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
def create_withdrawal(request):
    """Crear una solicitud de retiro: valida fondos, descuenta y crea el registro."""
    try:
        data = json.loads(request.body)
        amount_raw = data.get("amount")
        amount = Decimal(str(amount_raw)) if amount_raw is not None else Decimal('0')

        if amount <= 0:
            return JsonResponse({"error": "Cantidad inválida"}, status=400)

        profile = request.user.profile

        if profile.cosmos_gold < amount:
            return JsonResponse({"error": "Fondos insuficientes"}, status=400)

        with transaction.atomic():
            profile.cosmos_gold -= amount
            profile.save()

            wr = WithdrawalRequest.objects.create(
                user=request.user,
                amount=amount
            )

        return JsonResponse({"success": True, "id": wr.id, "amount": str(wr.amount), "created_at": wr.created_at.isoformat(), "status": wr.status})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        print("CREATE WITHDRAWAL ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def process_withdrawal(request, pk):
    """Aceptar o rechazar una solicitud (solo staff). Reembolsa si es rechazado."""
    try:
        data = json.loads(request.body)
        action = data.get("action")

        with transaction.atomic():
            wr = WithdrawalRequest.objects.select_for_update().get(pk=pk)

            if wr.status != WithdrawalRequest.STATUS_PENDING:
                return JsonResponse({"error": "Solicitud ya procesada"}, status=400)

            if action == "accept":
                wr.status = WithdrawalRequest.STATUS_ACCEPTED
                wr.processed_at = timezone.now()
                wr.processed_by = request.user
                wr.save()

            elif action == "reject":
                # reembolsar al usuario
                profile = wr.user.profile
                profile.cosmos_gold += wr.amount
                profile.save()

                wr.status = WithdrawalRequest.STATUS_REJECTED
                wr.processed_at = timezone.now()
                wr.processed_by = request.user
                wr.save()

            else:
                return JsonResponse({"error": "Acción inválida"}, status=400)

        return JsonResponse({"success": True, "status": wr.status})

    except WithdrawalRequest.DoesNotExist:
        return JsonResponse({"error": "Solicitud no encontrada"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        print("PROCESS WITHDRAWAL ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
def logout_view(request):
    from django.contrib.auth import logout
    try:
        logout(request)
        return JsonResponse({"success": True})
    except Exception as e:
        print("LOGOUT ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)