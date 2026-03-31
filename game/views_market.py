from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import MarketConfig, UserMarketExchange, Mineral, MarketGlobalSettings
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

def _parse_bool(value):
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "on", "yes"}

@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_admin_view(request):
    minerals = Mineral.objects.all().order_by('name')
    settings = MarketGlobalSettings.get_settings()
    return render(request, "game/market_admin.html", {
        "minerals": minerals,
        "settings": settings
    })

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_configs_list(request):
    items = []
    qs = MarketConfig.objects.all().select_related('mineral').order_by('mineral__name')
    for c in qs:
        items.append({
            "id": c.id,
            "mineral_id": c.mineral.id,
            "mineral_name": c.mineral.name,
            "gold_multiplier": float(c.gold_multiplier),
            "is_black": c.is_black,
            "is_active": c.is_active,
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_config_create(request):
    try:
        mineral_id = request.POST.get("mineral_id")
        gold_multiplier = Decimal(request.POST.get("gold_multiplier") or '0')
        is_black = _parse_bool(request.POST.get("is_black"))
        is_active = _parse_bool(request.POST.get("is_active"))
        
        if not mineral_id:
            return JsonResponse({"error": "Debe seleccionar un mineral"}, status=400)
            
        mineral = Mineral.objects.get(id=mineral_id)
        
        # We can have multiple configs per mineral if they are in different markets?
        # User request says: "grouped in 2 sections", so one mineral might be in Standard AND Black?
        # Or Just one? Let's check logic: config = MarketConfig.objects.filter(mineral_id=mid, is_black=is_black_request).first()
        # So it allows having same mineral in both.
        if MarketConfig.objects.filter(mineral=mineral, is_black=is_black).exists():
             return JsonResponse({"error": "Ya existe una configuración para este mineral en este mercado"}, status=400)

        MarketConfig.objects.create(
            mineral=mineral,
            gold_multiplier=gold_multiplier,
            is_black=is_black,
            is_active=is_active
        )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_config_update(request, pk):
    try:
        c = MarketConfig.objects.get(pk=pk)
        c.gold_multiplier = Decimal(request.POST.get("gold_multiplier") or '0')
        c.is_black = _parse_bool(request.POST.get("is_black"))
        c.is_active = _parse_bool(request.POST.get("is_active"))
        c.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_settings_update(request):
    try:
        settings = MarketGlobalSettings.get_settings()
        settings.standard_cooldown_hours = int(request.POST.get('standard_cooldown_hours', 864))
        settings.black_cooldown_hours = int(request.POST.get('black_cooldown_hours', 864))
        settings.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_exchanges_list(request):
    items = []
    qs = UserMarketExchange.objects.select_related("user", "mineral").order_by("-start_time")[:100]
    for ex in qs:
        items.append({
            "id": ex.id,
            "username": ex.user.username,
            "mineral": ex.mineral.name,
            "amount": ex.amount_mineral,
            "gold": float(ex.gold_expected),
            "end_time": ex.end_time.isoformat(),
            "is_claimed": ex.is_claimed,
            "is_ready": timezone.now() >= ex.end_time
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def market_exchange_delete(request, pk):
    try:
        ex = UserMarketExchange.objects.get(pk=pk)
        ex.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
