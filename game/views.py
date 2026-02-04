from django.shortcuts import render
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from .models import Profile, WithdrawalRequest, MinerType, UserMiner
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


@login_required
@user_passes_test(lambda u: u.is_staff)
def withdrawals_admin_view(request):
    if request.method == "GET":
        withdrawals = WithdrawalRequest.objects.select_related("user", "processed_by").order_by("-created_at")
        return render(request, "game/withdrawals_admin.html", {"withdrawals": withdrawals})
    return JsonResponse({"error": "Método no permitido"}, status=405)


@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard_view(request):
    if request.method == "GET":
        return render(request, "game/admin_dashboard.html")
    return JsonResponse({"error": "Método no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard_stats(request):
    try:
        from django.db.models import Sum
        total_users = User.objects.count()
        total_profiles = Profile.objects.count()
        total_miner_types = MinerType.objects.count()
        total_user_miners = UserMiner.objects.count()
        total_withdrawals = WithdrawalRequest.objects.count()
        pending_withdrawals = WithdrawalRequest.objects.filter(status=WithdrawalRequest.STATUS_PENDING).count()
        total_gold = Profile.objects.aggregate(total=Sum('cosmos_gold'))['total'] or 0

        recent_withdrawals = list(
            WithdrawalRequest.objects.select_related('user')
            .order_by('-created_at')
            .values('id', 'user__username', 'amount', 'status', 'created_at')[:8]
        )

        return JsonResponse({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_profiles': total_profiles,
                'total_miner_types': total_miner_types,
                'total_user_miners': total_user_miners,
                'total_withdrawals': total_withdrawals,
                'pending_withdrawals': pending_withdrawals,
                'total_gold': str(total_gold)
            },
            'recent_withdrawals': recent_withdrawals
        })
    except Exception as e:
        print('ADMIN DASHBOARD STATS ERROR:', e)
        return JsonResponse({"error": "Error interno"}, status=500)


@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def miners_admin_view(request):
    if request.method == "GET":
        return render(request, "game/miners_admin.html")
    return JsonResponse({"error": "M??todo no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def miners_admin_stats(request):
    try:
        users = list(User.objects.values("id", "username").order_by("username"))
        return JsonResponse({
            "success": True,
            "stats": {
                "total_miner_types": MinerType.objects.count(),
                "total_user_miners": UserMiner.objects.count()
            },
            "users": users
        })
    except Exception as e:
        print("MINERS ADMIN STATS ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


def _parse_bool(value):
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "on", "yes"}


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def miner_types_list(request):
    items = []
    for mt in MinerType.objects.all().order_by("-created_at"):
        items.append({
            "id": mt.id,
            "name": mt.name,
            "rarity": mt.rarity,
            "rarity_label": mt.get_rarity_display(),
            "attempts": mt.attempts,
            "is_active": mt.is_active,
            "image_url": mt.image.url if mt.image else ""
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def miner_type_create(request):
    try:
        name = (request.POST.get("name") or "").strip()
        rarity = (request.POST.get("rarity") or "").strip()
        attempts_raw = request.POST.get("attempts")
        is_active = _parse_bool(request.POST.get("is_active"))
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        valid_rarities = {c[0] for c in MinerType._meta.get_field("rarity").choices}
        if rarity not in valid_rarities:
            return JsonResponse({"error": "Rareza inv??lida"}, status=400)

        try:
            attempts = int(attempts_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Intentos inv??lidos"}, status=400)
        if attempts <= 0:
            return JsonResponse({"error": "Intentos inv??lidos"}, status=400)

        mt = MinerType.objects.create(
            name=name,
            rarity=rarity,
            attempts=attempts,
            is_active=is_active,
            image=image
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": mt.id,
                "name": mt.name,
                "rarity": mt.rarity,
                "rarity_label": mt.get_rarity_display(),
                "attempts": mt.attempts,
                "is_active": mt.is_active,
                "image_url": mt.image.url if mt.image else ""
            }
        })
    except Exception as e:
        print("MINER TYPE CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def miner_type_update(request, pk):
    try:
        mt = MinerType.objects.get(pk=pk)
        name = (request.POST.get("name") or "").strip()
        rarity = (request.POST.get("rarity") or "").strip()
        attempts_raw = request.POST.get("attempts")
        is_active = _parse_bool(request.POST.get("is_active"))
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        valid_rarities = {c[0] for c in MinerType._meta.get_field("rarity").choices}
        if rarity not in valid_rarities:
            return JsonResponse({"error": "Rareza inv??lida"}, status=400)

        try:
            attempts = int(attempts_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Intentos inv??lidos"}, status=400)
        if attempts <= 0:
            return JsonResponse({"error": "Intentos inv??lidos"}, status=400)

        mt.name = name
        mt.rarity = rarity
        mt.attempts = attempts
        mt.is_active = is_active
        if image:
            mt.image = image
        mt.save()

        return JsonResponse({
            "success": True,
            "item": {
                "id": mt.id,
                "name": mt.name,
                "rarity": mt.rarity,
                "rarity_label": mt.get_rarity_display(),
                "attempts": mt.attempts,
                "is_active": mt.is_active,
                "image_url": mt.image.url if mt.image else ""
            }
        })
    except MinerType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("MINER TYPE UPDATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def miner_type_toggle(request, pk):
    try:
        mt = MinerType.objects.get(pk=pk)
        mt.is_active = not mt.is_active
        mt.save()
        return JsonResponse({"success": True, "is_active": mt.is_active})
    except MinerType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("MINER TYPE TOGGLE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_miners_list(request):
    items = []
    q = UserMiner.objects.select_related("owner__user", "miner_type").order_by("-obtained_at")
    for um in q:
        items.append({
            "id": um.id,
            "user_id": um.owner.user.id,
            "username": um.owner.user.username,
            "miner_type_id": um.miner_type.id,
            "miner_type_name": um.miner_type.name,
            "status": um.status,
            "status_label": um.get_status_display(),
            "obtained_at": um.obtained_at.isoformat()
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_miner_create(request):
    try:
        user_id = request.POST.get("user_id")
        miner_type_id = request.POST.get("miner_type_id")
        status = (request.POST.get("status") or "").strip()

        if not user_id or not miner_type_id:
            return JsonResponse({"error": "Datos incompletos"}, status=400)

        valid_status = {c[0] for c in UserMiner._meta.get_field("status").choices}
        if status not in valid_status:
            return JsonResponse({"error": "Estado inv??lido"}, status=400)

        user = User.objects.get(pk=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        miner_type = MinerType.objects.get(pk=miner_type_id)

        um = UserMiner.objects.create(
            owner=profile,
            miner_type=miner_type,
            status=status
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": um.id,
                "user_id": um.owner.user.id,
                "username": um.owner.user.username,
                "miner_type_id": um.miner_type.id,
                "miner_type_name": um.miner_type.name,
                "status": um.status,
                "status_label": um.get_status_display(),
                "obtained_at": um.obtained_at.isoformat()
            }
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)
    except MinerType.DoesNotExist:
        return JsonResponse({"error": "MinerType no encontrado"}, status=404)
    except Exception as e:
        print("USER MINER CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_miner_delete(request, pk):
    try:
        um = UserMiner.objects.get(pk=pk)
        um.delete()
        return JsonResponse({"success": True})
    except UserMiner.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("USER MINER DELETE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


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
            balance_before = profile.cosmos_gold
            balance_after = balance_before - amount

            profile.cosmos_gold = balance_after
            profile.save()

            wr = WithdrawalRequest.objects.create(
                user=request.user,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after
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

        return JsonResponse({
            "success": True,
            "status": wr.status,
            "processed_by": wr.processed_by.username if wr.processed_by else None,
            "processed_at": wr.processed_at.isoformat() if wr.processed_at else None
        })

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


@login_required
def miners_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    miners = profile.miners.select_related("miner_type").order_by("-obtained_at")
    return render(request, "game/miners.html", {"profile": profile, "miners": miners})
