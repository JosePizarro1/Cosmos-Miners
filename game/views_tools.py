from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal, InvalidOperation
from .models import Profile, ToolType, UserTool


def _parse_bool(value):
    """Helper function to parse boolean values from form data."""
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "on", "yes"}


# ============================================
# TOOL ADMIN VIEWS
# ============================================

@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def tools_admin_view(request):
    if request.method == "GET":
        return render(request, "game/tools_admin.html")
    return JsonResponse({"error": "Método no permitido"}, status=405)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def tools_admin_stats(request):
    try:
        users = list(User.objects.values("id", "username").order_by("username"))
        return JsonResponse({
            "success": True,
            "stats": {
                "total_tool_types": ToolType.objects.count(),
                "total_user_tools": UserTool.objects.count()
            },
            "users": users
        })
    except Exception as e:
        print("TOOLS ADMIN STATS ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def tool_types_list(request):
    items = []
    for tt in ToolType.objects.all().order_by("-created_at"):
        items.append({
            "id": tt.id,
            "name": tt.name,
            "rarity": tt.rarity,
            "rarity_label": tt.get_rarity_display(),
            "production_multiplier": str(tt.production_multiplier),
            "success_bonus": str(tt.success_bonus),
            "is_active": tt.is_active,
            "image_url": tt.image.url if tt.image else ""
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def tool_type_create(request):
    try:
        name = (request.POST.get("name") or "").strip()
        rarity = (request.POST.get("rarity") or "").strip()
        production_multiplier_raw = request.POST.get("production_multiplier")
        success_bonus_raw = request.POST.get("success_bonus")
        is_active = _parse_bool(request.POST.get("is_active"))
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        valid_rarities = {c[0] for c in ToolType._meta.get_field("rarity").choices}
        if rarity not in valid_rarities:
            return JsonResponse({"error": "Rareza inválida"}, status=400)

        try:
            production_multiplier = Decimal(production_multiplier_raw)
            success_bonus = Decimal(success_bonus_raw) if success_bonus_raw else Decimal("0.00")
        except (TypeError, ValueError, InvalidOperation):
            return JsonResponse({"error": "Multiplicador o bonus inválidos"}, status=400)
        
        if production_multiplier <= 0:
            return JsonResponse({"error": "El multiplicador debe ser positivo"}, status=400)

        tt = ToolType.objects.create(
            name=name,
            rarity=rarity,
            production_multiplier=production_multiplier,
            success_bonus=success_bonus,
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
                "production_multiplier": str(tt.production_multiplier),
                "success_bonus": str(tt.success_bonus),
                "is_active": tt.is_active,
                "image_url": tt.image.url if tt.image else ""
            }
        })
    except Exception as e:
        print("TOOL TYPE CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def tool_type_update(request, pk):
    try:
        tt = ToolType.objects.get(pk=pk)
        name = (request.POST.get("name") or "").strip()
        rarity = (request.POST.get("rarity") or "").strip()
        production_multiplier_raw = request.POST.get("production_multiplier")
        success_bonus_raw = request.POST.get("success_bonus")
        is_active = _parse_bool(request.POST.get("is_active"))
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)

        valid_rarities = {c[0] for c in ToolType._meta.get_field("rarity").choices}
        if rarity not in valid_rarities:
            return JsonResponse({"error": "Rareza inválida"}, status=400)

        try:
            production_multiplier = Decimal(production_multiplier_raw)
            success_bonus = Decimal(success_bonus_raw) if success_bonus_raw else Decimal("0.00")
        except (TypeError, ValueError, InvalidOperation):
            return JsonResponse({"error": "Multiplicador o bonus inválidos"}, status=400)
        
        if production_multiplier <= 0:
            return JsonResponse({"error": "El multiplicador debe ser positivo"}, status=400)

        tt.name = name
        tt.rarity = rarity
        tt.production_multiplier = production_multiplier
        tt.success_bonus = success_bonus
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
                "production_multiplier": str(tt.production_multiplier),
                "success_bonus": str(tt.success_bonus),
                "is_active": tt.is_active,
                "image_url": tt.image.url if tt.image else ""
            }
        })
    except ToolType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("TOOL TYPE UPDATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def tool_type_toggle(request, pk):
    try:
        tt = ToolType.objects.get(pk=pk)
        tt.is_active = not tt.is_active
        tt.save()
        return JsonResponse({"success": True, "is_active": tt.is_active})
    except ToolType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("TOOL TYPE TOGGLE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_tools_list(request):
    items = []
    q = UserTool.objects.select_related("owner__user", "tool_type").order_by("-obtained_at")
    for ut in q:
        items.append({
            "id": ut.id,
            "user_id": ut.owner.user.id,
            "username": ut.owner.user.username,
            "tool_type_id": ut.tool_type.id,
            "tool_type_name": ut.tool_type.name,
            "status": ut.status,
            "status_label": ut.get_status_display(),
            "obtained_at": ut.obtained_at.isoformat()
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_tool_create(request):
    try:
        user_id = request.POST.get("user_id")
        tool_type_id = request.POST.get("tool_type_id")
        status = (request.POST.get("status") or "").strip()

        if not user_id or not tool_type_id:
            return JsonResponse({"error": "Datos incompletos"}, status=400)

        valid_status = {c[0] for c in UserTool._meta.get_field("status").choices}
        if status not in valid_status:
            return JsonResponse({"error": "Estado inválido"}, status=400)

        user = User.objects.get(pk=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        tool_type = ToolType.objects.get(pk=tool_type_id)

        ut = UserTool.objects.create(
            owner=profile,
            tool_type=tool_type,
            status=status
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": ut.id,
                "user_id": ut.owner.user.id,
                "username": ut.owner.user.username,
                "tool_type_id": ut.tool_type.id,
                "tool_type_name": ut.tool_type.name,
                "status": ut.status,
                "status_label": ut.get_status_display(),
                "obtained_at": ut.obtained_at.isoformat()
            }
        })
    except User.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)
    except ToolType.DoesNotExist:
        return JsonResponse({"error": "ToolType no encontrado"}, status=404)
    except Exception as e:
        print("USER TOOL CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_tool_delete(request, pk):
    try:
        ut = UserTool.objects.get(pk=pk)
        ut.delete()
        return JsonResponse({"success": True})
    except UserTool.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("USER TOOL DELETE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)
@login_required
def tools_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    tools = profile.tools.select_related("tool_type").order_by("-obtained_at")
    return render(request, "game/tools.html", {"profile": profile, "tools": tools})
