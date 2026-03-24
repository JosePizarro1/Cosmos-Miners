from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Profile, OilCentralType, UserOilCentral
from decimal import Decimal
import random
from django.db import transaction

def _parse_bool(value):
    """Helper function to parse boolean values from form data."""
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "on", "yes"}

@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def oil_admin_view(request):
    """Render the Oil Centrals Admin page."""
    from .models_planets import Mineral
    minerals = Mineral.objects.all().order_by('name')
    return render(request, "game/oil_admin.html", {"minerals": minerals})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def oil_admin_stats(request):
    """Get stats for Oil Centrals."""
    try:
        users = list(User.objects.values("id", "username").order_by("username"))
        return JsonResponse({
            "success": True,
            "stats": {
                "total_oil_types": OilCentralType.objects.count(),
                "total_user_oil": UserOilCentral.objects.count()
            },
            "users": users
        })
    except Exception as e:
        print("OIL ADMIN STATS ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def oil_types_list(request):
    """List all available Oil Central types."""
    items = []
    for ot in OilCentralType.objects.all().order_by("-created_at"):
        items.append({
            "id": ot.id,
            "name": ot.name,
            "price_gold": float(ot.price_gold),
            "min_life_days": ot.min_life_days,
            "max_life_days": ot.max_life_days,
            "min_barrels_24h": float(ot.min_barrels_24h),
            "max_barrels_24h": float(ot.max_barrels_24h),
            "min_refined_24h": float(ot.min_refined_24h),
            "max_refined_24h": float(ot.max_refined_24h),
            "purchase_mineral_id": ot.purchase_mineral.id if ot.purchase_mineral else "",
            "purchase_mineral_name": ot.purchase_mineral.name if ot.purchase_mineral else "",
            "purchase_mineral_qty": ot.purchase_mineral_qty,
            "refined_mineral_id": ot.refined_mineral.id if ot.refined_mineral else "",
            "refined_mineral_name": ot.refined_mineral.name if ot.refined_mineral else "Ninguno",
            "is_active": ot.is_active,
            "image_url": ot.image.url if ot.image else ""
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def oil_type_create(request):
    """Create a new Oil Central type."""
    try:
        name = (request.POST.get("name") or "").strip()
        price_gold = request.POST.get("price_gold")
        min_life = request.POST.get("min_life_days")
        max_life = request.POST.get("max_life_days")
        min_barrels = request.POST.get("min_barrels_24h")
        max_barrels = request.POST.get("max_barrels_24h")
        min_refined = request.POST.get("min_refined_24h")
        max_refined = request.POST.get("max_refined_24h")
        is_active = _parse_bool(request.POST.get("is_active"))
        refined_mineral_id = request.POST.get("refined_mineral_id")
        image = request.FILES.get("image")

        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)
            
        from .models_planets import Mineral
        mineral = None
        if refined_mineral_id:
            mineral = Mineral.objects.filter(id=refined_mineral_id).first()

        purchase_mineral_id = request.POST.get("purchase_mineral_id")
        purchase_mineral_qty = int(request.POST.get("purchase_mineral_qty") or 0)
        
        purchase_m = Mineral.objects.filter(id=purchase_mineral_id).first() if purchase_mineral_id else None

        ot = OilCentralType.objects.create(
            name=name,
            price_gold=Decimal(price_gold or '0'),
            purchase_mineral=purchase_m,
            purchase_mineral_qty=purchase_mineral_qty,
            min_life_days=int(min_life or 0),
            max_life_days=int(max_life or 0),
            min_barrels_24h=Decimal(min_barrels or '0'),
            max_barrels_24h=Decimal(max_barrels or '0'),
            min_refined_24h=Decimal(min_refined or '0'),
            max_refined_24h=Decimal(max_refined or '0'),
            refined_mineral=mineral,
            is_active=is_active,
            image=image
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": ot.id,
                "name": ot.name,
                "price_gold": float(ot.price_gold),
                "min_life_days": ot.min_life_days,
                "max_life_days": ot.max_life_days,
                "min_barrels_24h": float(ot.min_barrels_24h),
                "max_barrels_24h": float(ot.max_barrels_24h),
                "min_refined_24h": float(ot.min_refined_24h),
                "max_refined_24h": float(ot.max_refined_24h),
                "is_active": ot.is_active,
                "image_url": ot.image.url if ot.image else ""
            }
        })
    except Exception as e:
        print("OIL TYPE CREATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def oil_type_update(request, pk):
    """Update an existing Oil Central type."""
    try:
        ot = OilCentralType.objects.get(pk=pk)
        ot.name = (request.POST.get("name") or "").strip()
        ot.price_gold = Decimal(request.POST.get("price_gold") or '0')
        ot.min_life_days = int(request.POST.get("min_life_days") or 0)
        ot.max_life_days = int(request.POST.get("max_life_days") or 0)
        ot.min_barrels_24h = Decimal(request.POST.get("min_barrels_24h") or '0')
        ot.max_barrels_24h = Decimal(request.POST.get("max_barrels_24h") or '0')
        ot.min_refined_24h = Decimal(request.POST.get("min_refined_24h") or '0')
        ot.max_refined_24h = Decimal(request.POST.get("max_refined_24h") or '0')
        ot.is_active = _parse_bool(request.POST.get("is_active"))
        
        refined_mineral_id = request.POST.get("refined_mineral_id")
        
        from .models_planets import Mineral
        if refined_mineral_id:
            ot.refined_mineral = Mineral.objects.filter(id=refined_mineral_id).first()
        else:
            ot.refined_mineral = None
            
        purchase_mineral_id = request.POST.get("purchase_mineral_id")
        if purchase_mineral_id:
            ot.purchase_mineral = Mineral.objects.filter(id=purchase_mineral_id).first()
        else:
            ot.purchase_mineral = None
            
        ot.purchase_mineral_qty = int(request.POST.get("purchase_mineral_qty") or 0)
        
        image = request.FILES.get("image")
        if image:
            ot.image = image
        
        ot.save()

        return JsonResponse({
            "success": True,
            "item": {
                "id": ot.id,
                "name": ot.name,
                "price_gold": float(ot.price_gold),
                "min_life_days": ot.min_life_days,
                "max_life_days": ot.max_life_days,
                "min_barrels_24h": float(ot.min_barrels_24h),
                "max_barrels_24h": float(ot.max_barrels_24h),
                "min_refined_24h": float(ot.min_refined_24h),
                "max_refined_24h": float(ot.max_refined_24h),
                "is_active": ot.is_active,
                "image_url": ot.image.url if ot.image else ""
            }
        })
    except OilCentralType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        print("OIL TYPE UPDATE ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def oil_type_toggle(request, pk):
    """Toggle the active status of an Oil Central type."""
    try:
        ot = OilCentralType.objects.get(pk=pk)
        ot.is_active = not ot.is_active
        ot.save()
        return JsonResponse({"success": True, "is_active": ot.is_active})
    except OilCentralType.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_oil_list(request):
    """List all instances of Oil Centrals owned by users."""
    items = []
    q = UserOilCentral.objects.select_related("owner__user", "central_type").order_by("-obtained_at")
    for uo in q:
        items.append({
            "id": uo.id,
            "username": uo.owner.user.username,
            "central_name": uo.central_type.name,
            "remaining_life": uo.remaining_life_days,
            "barrels_24h": float(uo.barrels_24h),
            "refined_24h": float(uo.refined_24h),
            "refining_status": uo.refining_status,
            "obtained_at": uo.obtained_at.isoformat()
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_oil_delete(request, pk):
    """Delete a user-owned Oil Central."""
    try:
        uo = UserOilCentral.objects.get(pk=pk)
        uo.delete()
        return JsonResponse({"success": True})
    except UserOilCentral.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
def buy_oil_central(request, type_id):
    """View to handle the purchase of an Oil Central."""
    try:
        central_type = OilCentralType.objects.get(id=type_id, is_active=True)
        profile = request.user.profile
        
        from .models_planets import UserMineral
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(id=profile.id)
            
            if central_type.purchase_mineral:
                req_qty = central_type.purchase_mineral_qty
                user_mineral = UserMineral.objects.select_for_update().filter(user=request.user, mineral=central_type.purchase_mineral).first()
                if not user_mineral or user_mineral.amount < req_qty:
                    return JsonResponse({"error": f"No tienes suficiente {central_type.purchase_mineral.name} ({req_qty} requeridos)"}, status=400)
                
                user_mineral.amount -= req_qty
                user_mineral.save()
            else:
                if profile.cosmos_gold < central_type.price_gold:
                    return JsonResponse({"error": "No tienes suficiente Cosmos Gold"}, status=400)
                    
                profile.cosmos_gold -= central_type.price_gold
                profile.save()
            
            # Randomize values based on defined ranges
            life_days = random.randint(central_type.min_life_days, central_type.max_life_days)
            
            def get_rand_int(min_v, max_v):
                min_i = int(min_v)
                max_i = int(max_v)
                if min_i >= max_i:
                    return Decimal(str(min_i))
                return Decimal(str(random.randint(min_i, max_i)))
                
            barrels_24h = get_rand_int(central_type.min_barrels_24h, central_type.max_barrels_24h)
            refined_24h = get_rand_int(central_type.min_refined_24h, central_type.max_refined_24h)
            
            # Create the instance for the user
            user_central = UserOilCentral.objects.create(
                owner=profile,
                central_type=central_type,
                initial_life_days=life_days,
                remaining_life_days=life_days,
                barrels_24h=barrels_24h,
                refined_24h=refined_24h
            )
            
        return JsonResponse({
            "success": True,
            "result": {
                "name": central_type.name,
                "life_days": life_days,
                "barrels_24h": float(barrels_24h),
                "refined_24h": float(refined_24h),
                "image_url": central_type.image.url if central_type.image else ""
            }
        })
    except OilCentralType.DoesNotExist:
        return JsonResponse({"error": "Central no disponible"}, status=404)
    except Exception as e:
        print("BUY OIL ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@login_required
def user_oil_view(request):
    """View for users to see their owned Oil Centrals."""
    from .models_planets import UserMineral, Mineral
    
    profile, _ = Profile.objects.get_or_create(user=request.user)
    centrals = profile.oil_centrals.select_related("central_type").order_by("-obtained_at")
    
    # Get oil barrels amount
    barrel_mineral = Mineral.objects.filter(name="Barril de Petróleo").first()
    oil_barrels = 0
    if barrel_mineral:
        um = UserMineral.objects.filter(user=request.user, mineral=barrel_mineral).first()
        if um:
            oil_barrels = um.amount
            
    return render(request, "game/oil.html", {
        "profile": profile, 
        "centrals": centrals,
        "oil_barrels": oil_barrels
    })

@require_POST
@csrf_protect
@login_required
def claim_oil_barrels(request, pk):
    """Claim daily oil barrels from a central."""
    from datetime import timedelta
    from django.utils import timezone
    from .models_planets import Mineral, UserMineral

    try:
        uo = UserOilCentral.objects.select_for_update().get(pk=pk, owner=request.user.profile)
        now = timezone.now()
        
        # Validation
        if uo.remaining_life_days <= 0:
            return JsonResponse({"error": "Esta central ha agotado su vida útil."}, status=400)
            
        next_claim = uo.last_collection + timedelta(hours=24)
        if now < next_claim:
            remaining = next_claim - now
            h, m = divmod(int(remaining.total_seconds()), 3600)
            m, s = divmod(m, 60)
            return JsonResponse({"error": f"Faltan {h}h {m}m para el próximo reclamo."}, status=400)

        with transaction.atomic():
            # Get or create the Oil Barrel mineral
            barrel_mineral, _ = Mineral.objects.get_or_create(
                name="Barril de Petróleo",
                defaults={"description": "Un barril lleno de petróleo crudo extraído de las profundidades planetarias."}
            )
            
            user_inv, _ = UserMineral.objects.get_or_create(user=request.user, mineral=barrel_mineral)
            
            # Add barrels (integer amount as requested)
            amount = int(uo.barrels_24h)
            user_inv.amount += amount
            user_inv.save()
            
            # Update central
            uo.last_collection = now
            uo.remaining_life_days -= 1
            uo.save()
            
        return JsonResponse({
            "success": True,
            "claimed": amount,
            "remaining_life": uo.remaining_life_days,
            "remaining_life_perc": uo.get_life_percentage
        })
    except UserOilCentral.DoesNotExist:
        return JsonResponse({"error": "Central no encontrada"}, status=404)
    except Exception as e:
        print("CLAIM OIL BARRELS ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_oil_force_ready(request, pk):
    """Admin tool to force an oil central to be ready for claim (resets 24h timer)."""
    from datetime import timedelta
    from django.utils import timezone
    try:
        uo = UserOilCentral.objects.get(pk=pk)
        # Set last_collection to 25 hours ago
        uo.last_collection = timezone.now() - timedelta(hours=25)
        uo.save()
        return JsonResponse({"success": True})
    except UserOilCentral.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_oil_force_refine_ready(request, pk):
    """Admin tool to force an oil central's refining process to finish."""
    from datetime import timedelta
    from django.utils import timezone
    try:
        uo = UserOilCentral.objects.get(pk=pk)
        if uo.refining_status == 'refining':
            # Set refining start time to far in the past to bypass cooldown
            uo.refining_start_time = timezone.now() - timedelta(hours=800)
            uo.save()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Esta central no está refinando"}, status=400)
    except UserOilCentral.DoesNotExist:
        return JsonResponse({"error": "No encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
def start_refining(request, pk):
    """Start refining process for an oil central if conditions are met."""
    from .models_planets import Mineral, UserMineral
    from django.utils import timezone
    from django.db import transaction
    try:
        uo = UserOilCentral.objects.select_for_update().get(pk=pk, owner=request.user.profile)
        
        if uo.refining_charges <= 0:
            return JsonResponse({"error": "No te quedan cargas de refinación en esta central."}, status=400)
            
        if uo.refining_status == 'refining':
            return JsonResponse({"error": "Esta central ya está refinando."}, status=400)
            
        required_barrels = int(uo.refined_24h)
        barrel_mineral = Mineral.objects.filter(name="Barril de Petróleo").first()
        if not barrel_mineral:
            return JsonResponse({"error": "El mineral 'Barril de Petróleo' no existe."}, status=400)
            
        user_inv, _ = UserMineral.objects.get_or_create(user=request.user, mineral=barrel_mineral)
        if user_inv.amount < required_barrels:
            return JsonResponse({"error": f"Necesitas {required_barrels} barriles para refinar, pero solo tienes {user_inv.amount}."}, status=400)
            
        with transaction.atomic():
            # Deduct barrels
            user_inv.amount -= required_barrels
            user_inv.save()
            
            # Update central
            uo.refining_charges -= 1
            uo.refining_status = 'refining'
            uo.refining_start_time = timezone.now()
            uo.save()
            
        # Return new state
        return JsonResponse({
            "success": True,
            "refining_charges": uo.refining_charges,
            "refining_status": uo.refining_status,
            "refine_countdown": uo.refine_countdown
        })
    except UserOilCentral.DoesNotExist:
        return JsonResponse({"error": "Central no encontrada"}, status=404)
    except Exception as e:
        print("START REFINING ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)

@require_POST
@csrf_protect
@login_required
def claim_refinement(request, pk):
    """Claim the refined mineral after the cooldown has finished."""
    from .models_planets import Mineral, UserMineral
    from django.utils import timezone
    from datetime import timedelta
    from django.db import transaction
    
    try:
        uo = UserOilCentral.objects.select_for_update().get(pk=pk, owner=request.user.profile)
        
        if uo.refining_status != 'refining':
            return JsonResponse({"error": "Esta central no está refinando o no está lista."}, status=400)
            
        if uo.refine_countdown > 0:
            return JsonResponse({"error": "Aún no ha terminado la refinación."}, status=400)
            
        # Get the mineral reward
        reward_mineral = uo.central_type.refined_mineral
        if not reward_mineral:
            return JsonResponse({"error": "Esta central no tiene un mineral configurado para refinar."}, status=400)
            
        reward_qty = int(uo.refined_24h)
            
        with transaction.atomic():
            # Add reward mineral to inventory
            user_inv, _ = UserMineral.objects.get_or_create(user=request.user, mineral=reward_mineral)
            user_inv.amount += reward_qty
            user_inv.save()
            
            # Update central
            uo.refining_status = 'idle'
            uo.refining_start_time = None
            uo.save()
            
        return JsonResponse({
            "success": True,
            "claimed_mineral": reward_mineral.name,
            "claimed_qty": reward_qty,
            "refining_charges": uo.refining_charges,
            "refining_status": uo.refining_status
        })
    except UserOilCentral.DoesNotExist:
        return JsonResponse({"error": "Central no encontrada"}, status=404)
    except Exception as e:
        print("CLAIM REFINEMENT ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)
