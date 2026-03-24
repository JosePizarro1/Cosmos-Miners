from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import TradeOffer, UserActiveTrade, UserMineral, Profile, Mineral
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

def _parse_bool(value):
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "on", "yes"}

@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def trades_admin_view(request):
    minerals = Mineral.objects.all().order_by('name')
    return render(request, "game/trades_admin.html", {"minerals": minerals})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def trade_offers_list(request):
    items = []
    for t in TradeOffer.objects.all().order_by("-created_at"):
        items.append({
            "id": t.id,
            "mineral_id": t.mineral.id,
            "mineral_name": t.mineral.name,
            "mineral_qty": t.mineral_qty,
            "gold_reward": float(t.gold_reward),
            "duration_hours": t.duration_hours,
            "is_active": t.is_active,
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def trade_offer_create(request):
    try:
        mineral_id = request.POST.get("mineral_id")
        mineral_qty = int(request.POST.get("mineral_qty") or 0)
        gold_reward = Decimal(request.POST.get("gold_reward") or '0')
        duration_hours = int(request.POST.get("duration_hours") or 0)
        is_active = _parse_bool(request.POST.get("is_active"))
        
        if not mineral_id:
            return JsonResponse({"error": "Debe seleccionar un mineral"}, status=400)
            
        mineral = Mineral.objects.get(id=mineral_id)
        
        t = TradeOffer.objects.create(
            mineral=mineral,
            mineral_qty=mineral_qty,
            gold_reward=gold_reward,
            duration_hours=duration_hours,
            is_active=is_active
        )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def trade_offer_update(request, pk):
    try:
        t = TradeOffer.objects.get(pk=pk)
        mineral_id = request.POST.get("mineral_id")
        if mineral_id:
            t.mineral = Mineral.objects.get(id=mineral_id)
            
        t.mineral_qty = int(request.POST.get("mineral_qty") or 0)
        t.gold_reward = Decimal(request.POST.get("gold_reward") or '0')
        t.duration_hours = int(request.POST.get("duration_hours") or 0)
        t.is_active = _parse_bool(request.POST.get("is_active"))
        t.save()
        
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def trade_offer_toggle(request, pk):
    try:
        t = TradeOffer.objects.get(pk=pk)
        t.is_active = not t.is_active
        t.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_trades_list(request):
    items = []
    qs = UserActiveTrade.objects.select_related("user", "offer__mineral").order_by("-start_time")
    for ut in qs:
        items.append({
            "id": ut.id,
            "username": ut.user.username,
            "mineral": ut.offer.mineral.name,
            "qty": ut.offer.mineral_qty,
            "gold": float(ut.offer.gold_reward),
            "start_time": ut.start_time.isoformat(),
            "end_time": ut.end_time.isoformat(),
            "is_claimed": ut.is_claimed,
            "is_finished": timezone.now() >= ut.end_time
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_trade_delete(request, pk):
    try:
        ut = UserActiveTrade.objects.get(pk=pk)
        ut.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Public Views
@ensure_csrf_cookie
@login_required
def trades_public_view(request):
    active_trade = UserActiveTrade.objects.filter(user=request.user, is_claimed=False).first()
    inventory = {um.mineral_id: um.amount for um in UserMineral.objects.filter(user=request.user)}
    
    offers_list = []
    for offer in TradeOffer.objects.filter(is_active=True).order_by('duration_hours'):
        offer.user_qty = inventory.get(offer.mineral_id, 0)
        offers_list.append(offer)
    
    return render(request, "game/trades_public.html", {
        "offers": offers_list,
        "active_trade": active_trade,
        "now": timezone.now()
    })

@require_POST
@csrf_protect
@login_required
def start_trade(request, offer_id):
    try:
        offer = TradeOffer.objects.get(id=offer_id, is_active=True)
        
        # Check if user already has an active trade globally
        if UserActiveTrade.objects.filter(user=request.user, is_claimed=False).exists():
            return JsonResponse({"error": "Ya tienes una venta en progreso. Espera a que termine."}, status=400)
            
        with transaction.atomic():
            # Check inventory
            user_mineral = UserMineral.objects.select_for_update().filter(user=request.user, mineral=offer.mineral).first()
            if not user_mineral or user_mineral.amount < offer.mineral_qty:
                return JsonResponse({"error": "No tienes suficientes unidades de mineral para esta venta."}, status=400)
                
            # Deduct mineral
            user_mineral.amount -= offer.mineral_qty
            user_mineral.save()
            
            # Create active trade
            end_t = timezone.now() + timedelta(hours=offer.duration_hours)
            UserActiveTrade.objects.create(
                user=request.user,
                offer=offer,
                end_time=end_t
            )
            
        return JsonResponse({"success": True})
    except TradeOffer.DoesNotExist:
        return JsonResponse({"error": "Oferta no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
def claim_trade(request, trade_id):
    try:
        with transaction.atomic():
            ut = UserActiveTrade.objects.select_for_update().get(id=trade_id, user=request.user, is_claimed=False)
            
            if timezone.now() < ut.end_time:
                return JsonResponse({"error": "Aún no expira el tiempo de venta."}, status=400)
                
            profile = Profile.objects.select_for_update().get(id=request.user.profile.id)
            profile.cosmos_gold += ut.offer.gold_reward
            profile.save()
            
            ut.is_claimed = True
            ut.save()
            
            return JsonResponse({
                "success": True,
                "reward": float(ut.offer.gold_reward)
            })
    except UserActiveTrade.DoesNotExist:
        return JsonResponse({"error": "Venta no existe o ya fue reclamada."}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def force_ready_trade(request, pk):
    try:
        ut = UserActiveTrade.objects.get(pk=pk, is_claimed=False)
        ut.end_time = timezone.now()
        ut.save()
        return JsonResponse({"success": True})
    except UserActiveTrade.DoesNotExist:
        return JsonResponse({"error": "No valido"}, status=404)
