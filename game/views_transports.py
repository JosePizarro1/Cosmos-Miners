from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Profile, TransportType, UserTransport


def _parse_bool(value):
    """Helper function to parse boolean values from form data."""
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "on", "yes"}


# ============================================
# TRANSPORT ADMIN VIEWS
# ============================================

@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def transports_admin_view(request):
    if request.method == "GET":
        return render(request, "game/transports_admin.html")
    return JsonResponse({"error": "Método no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def transports_admin_stats(request):
    try:
        users = list(User.objects.values("id", "username").order_by("username"))
        return JsonResponse({
            "success": True,
            "stats": {
                "total_transport_types": TransportType.objects.count(),
                "total_user_transports": UserTransport.objects.count()
            },
            "users": users
        })
    except Exception as e:
        print("TRANSPORTS ADMIN STATS ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def transport_types_list(request):
    items = []
    for tt in TransportType.objects.all().order_by("-created_at"):
        items.append({
            "id": tt.id,
            "name": tt.name,
            "rarity": tt.rarity,
            "rarity_label": tt.get_rarity_display(),
            "capacity": tt.capacity,
            "speed": tt.speed,
            "is_active": tt.is_active,
            "image_url": tt.image.url if tt.image else ""
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def transport_type_create(request):
    try:
        name = (request.POST.get("name") or "").strip()
        rarity = (request.POST.get("rarity") or "").strip()
        capacity_raw = request.POST.get("capacity")
        speed_raw = request.POST.get("speed")
        is_active = _parse_bool(request.POST.get("is_active"))
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        valid_rarities = {c[0] for c in TransportType._meta.get_field("rarity").choices}
        if rarity not in valid_rarities:
            return JsonResponse({"error": "Rareza inválida"}, status=400)

        try:
            capacity = int(capacity_raw)
            speed = int(speed_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Capacidad o velocidad inválidos"}, status=400)
        if capacity <= 0 or speed <= 0:
            return JsonResponse({"error": "Capacidad y velocidad deben ser positivos"}, status=400)

        tt = TransportType.objects.create(
            name=name,
            rarity=rarity,
            capacity=capacity,
            speed=speed,
            is_active=is_active,
            image=image
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": tt.id,
                "name": tt.name,
                "rarity": tt.rarity,
                "rarity_label": tt.get_rarity_display(),
                "capacity": tt.capacity,
                "speed": tt.speed,
                "is_active": tt.is_active,
                "image_url": tt.image.url if tt.image else ""
            }
        })
    except Exception as e:
        print("TRANSPORT TYPE CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def transport_type_update(request, pk):
    try:
        tt = TransportType.objects.get(pk=pk)
        name = (request.POST.get("name") or "").strip()
        rarity = (request.POST.get("rarity") or "").strip()
        capacity_raw = request.POST.get("capacity")
        speed_raw = request.POST.get("speed")
        is_active = _parse_bool(request.POST.get("is_active"))
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        valid_rarities = {c[0] for c in TransportType._meta.get_field("rarity").choices}
        if rarity not in valid_rarities:
            return JsonResponse({"error": "Rareza inválida"}, status=400)

        try:
            capacity = int(capacity_raw)
            speed = int(speed_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Capacidad o velocidad inválidos"}, status=400)
        if capacity <= 0 or speed <= 0:
            return JsonResponse({"error": "Capacidad y velocidad deben ser positivos"}, status=400)

        tt.name = name
        tt.rarity = rarity
        tt.capacity = capacity
        tt.speed = speed
        tt.is_active = is_active
        if image:
            tt.image = image
        tt.save()

        return JsonResponse({
            "success": True,
            "item": {
                "id": tt.id,
                "name": tt.name,
                "rarity": tt.rarity,
                "rarity_label": tt.get_rarity_display(),
                "capacity": tt.capacity,
                "speed": tt.speed,
                "is_active": tt.is_active,
                "image_url": tt.image.url if tt.image else ""
            }
        })
    except TransportType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("TRANSPORT TYPE UPDATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def transport_type_toggle(request, pk):
    try:
        tt = TransportType.objects.get(pk=pk)
        tt.is_active = not tt.is_active
        tt.save()
        return JsonResponse({"success": True, "is_active": tt.is_active})
    except TransportType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("TRANSPORT TYPE TOGGLE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_transports_list(request):
    items = []
    q = UserTransport.objects.select_related("owner__user", "transport_type").order_by("-obtained_at")
    for ut in q:
        items.append({
            "id": ut.id,
            "user_id": ut.owner.user.id,
            "username": ut.owner.user.username,
            "transport_type_id": ut.transport_type.id,
            "transport_type_name": ut.transport_type.name,
            "status": ut.status,
            "status_label": ut.get_status_display(),
            "obtained_at": ut.obtained_at.isoformat()
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_transport_create(request):
    try:
        user_id = request.POST.get("user_id")
        transport_type_id = request.POST.get("transport_type_id")
        status = (request.POST.get("status") or "").strip()

        if not user_id or not transport_type_id:
            return JsonResponse({"error": "Datos incompletos"}, status=400)

        valid_status = {c[0] for c in UserTransport._meta.get_field("status").choices}
        if status not in valid_status:
            return JsonResponse({"error": "Estado inválido"}, status=400)

        user = User.objects.get(pk=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        transport_type = TransportType.objects.get(pk=transport_type_id)

        ut = UserTransport.objects.create(
            owner=profile,
            transport_type=transport_type,
            status=status
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": ut.id,
                "user_id": ut.owner.user.id,
                "username": ut.owner.user.username,
                "transport_type_id": ut.transport_type.id,
                "transport_type_name": ut.transport_type.name,
                "status": ut.status,
                "status_label": ut.get_status_display(),
                "obtained_at": ut.obtained_at.isoformat()
            }
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)
    except TransportType.DoesNotExist:
        return JsonResponse({"error": "TransportType no encontrado"}, status=404)
    except Exception as e:
        print("USER TRANSPORT CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_transport_delete(request, pk):
    try:
        ut = UserTransport.objects.get(pk=pk)
        ut.delete()
        return JsonResponse({"success": True})
    except UserTransport.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("USER TRANSPORT DELETE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


# ============================================
# TRANSPORT USER VIEWS
# ============================================

@login_required
def transports_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    transports = profile.transports.select_related("transport_type").order_by("-obtained_at")
    return render(request, "game/transports.html", {"profile": profile, "transports": transports})
