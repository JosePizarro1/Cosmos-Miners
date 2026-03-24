from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models_blessings import Blessing, StaticBlessing, UserBlessingClaim, UserDynamicBlessing
from .models import Profile, UserOilCentral, Season, UserSeasonEntry
from .models_packs import StorePack, PackPurchaseLog
from .models_planets import Mineral, UserMineral
from decimal import Decimal
import datetime
from datetime import timedelta

@login_required
@user_passes_test(lambda u: u.is_staff)
def blessings_admin_view(request):
    # Asegurar que las 4 estáticas existan
    StaticBlessing.objects.get_or_create(type='oil', defaults={'name': 'Bendición del Petróleo', 'bonus_percentage': 1.0})
    StaticBlessing.objects.get_or_create(type='vip', defaults={'name': 'Bendición VIP', 'bonus_percentage': 0.0})
    StaticBlessing.objects.get_or_create(type='cosmos', defaults={'name': 'Bendición Cosmos', 'bonus_percentage': 2.0})
    StaticBlessing.objects.get_or_create(type='extra', defaults={'name': 'Bendición Extra', 'bonus_percentage': 0.0})

    static_blessings = StaticBlessing.objects.all()
    dynamic_blessings = Blessing.objects.all().order_by('-created_at')
    minerals = Mineral.objects.all()
    packs = StorePack.objects.all()

    return render(request, "game/blessings_admin.html", {
        "static_blessings": static_blessings,
        "dynamic_blessings": dynamic_blessings,
        "minerals": minerals,
        "packs": packs
    })

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def blessing_create(request):
    try:
        data = request.POST
        blessing = Blessing.objects.create(
            name=data.get("name"),
            price_gold=Decimal(data.get("price_gold") or 0),
            price_mineral_id=data.get("price_mineral_id") or None,
            price_mineral_qty=Decimal(data.get("price_mineral_qty") or 0),
            reward_mineral_id=data.get("reward_mineral_id") or None,
            reward_mineral_qty=Decimal(data.get("reward_mineral_qty") or 0),
            reward_gold=Decimal(data.get("reward_gold") or 0),
            cooldown_hours=int(data.get("cooldown_hours") or 24),
            is_active=data.get("is_active") == "on"
        )
        if 'image' in request.FILES:
            blessing.image = request.FILES['image']
            blessing.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def static_blessing_update(request, pk):
    try:
        sb = StaticBlessing.objects.get(pk=pk)
        sb.name = request.POST.get("name")
        sb.bonus_percentage = Decimal(request.POST.get("bonus_percentage") or 0)
        if sb.type == 'cosmos':
            pack_id = request.POST.get("required_pack_id")
            sb.required_pack_id = pack_id if pack_id else None
        sb.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def blessing_update(request, pk):
    try:
        data = request.POST
        blessing = Blessing.objects.get(pk=pk)
        blessing.name = data.get("name")
        blessing.price_gold = Decimal(data.get("price_gold") or 0)
        
        mineral_id = data.get("price_mineral_id")
        blessing.price_mineral_id = mineral_id if mineral_id else None
        blessing.price_mineral_qty = Decimal(data.get("price_mineral_qty") or 0)

        rew_mineral_id = data.get("reward_mineral_id")
        blessing.reward_mineral_id = rew_mineral_id if rew_mineral_id else None
        blessing.reward_mineral_qty = Decimal(data.get("reward_mineral_qty") or 0)
        
        blessing.reward_gold = Decimal(data.get("reward_gold") or 0)
        
        blessing.cooldown_hours = int(data.get("cooldown_hours") or 24)
        blessing.is_active = data.get("is_active") == "on"
        
        if 'image' in request.FILES:
            blessing.image = request.FILES['image']
        
        blessing.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def blessing_delete(request, pk):
    try:
        blessing = Blessing.objects.get(pk=pk)
        blessing.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# PUBLIC VIEWS

@require_POST
@login_required
def claim_blessing(request, blessing_type, blessing_id):
    """Reclama una bendición (estática o dinámica)."""
    try:
        user = request.user
        profile = user.profile

        if blessing_type == 'static':
            try:
                sb = StaticBlessing.objects.get(pk=blessing_id)
            except StaticBlessing.DoesNotExist:
                return JsonResponse({"error": "Bendición no encontrada."}, status=404)

            # Requisitos específicos
            if sb.type == 'oil':
                if not UserOilCentral.objects.filter(owner=profile).exists():
                    return JsonResponse({"error": "Debes tener al menos una central petrolera."}, status=400)
            elif sb.type == 'vip':
                if not UserSeasonEntry.objects.filter(user=user).exists():
                    return JsonResponse({"error": "Debes inscribirte en al menos un ranking."}, status=400)
            elif sb.type == 'cosmos':
                if not sb.required_pack:
                    return JsonResponse({"error": "Esta bendición no está configurada correctamente (falta pack)."}, status=400)
                if not PackPurchaseLog.objects.filter(user=user, pack=sb.required_pack).exists():
                    return JsonResponse({"error": f"Debes adquirir el paquete: {sb.required_pack.name}."}, status=400)
            
            # Ya reclamada?
            if UserBlessingClaim.objects.filter(user=user, static_blessing=sb).exists():
                return JsonResponse({"error": "Ya has reclamado esta bendición."}, status=400)
            
            UserBlessingClaim.objects.create(user=user, static_blessing=sb)
            return JsonResponse({"success": True, "message": "¡Bendición reclamada con éxito!"})

        elif blessing_type == 'dynamic':
            try:
                b = Blessing.objects.get(pk=blessing_id, is_active=True)
            except Blessing.DoesNotExist:
                return JsonResponse({"error": "Bendición no encontrada."}, status=404)
            
            # Check ownership
            if UserDynamicBlessing.objects.filter(user=user, blessing=b).exists():
                return JsonResponse({"error": "Ya posees esta bendición. Ve a Inicio para farmearla."}, status=400)

            # Check cost
            if b.price_mineral and b.price_mineral_qty > 0:
                um = UserMineral.objects.filter(user=user, mineral=b.price_mineral).first()
                if not um or um.amount < b.price_mineral_qty:
                    return JsonResponse({"error": f"No tienes suficiente {b.price_mineral.name}."}, status=400)
                um.amount -= b.price_mineral_qty
                um.save()
            elif b.price_gold > 0:
                if profile.cosmos_gold < b.price_gold:
                    return JsonResponse({"error": "No tienes suficiente Cosmos Gold."}, status=400)
                profile.cosmos_gold -= b.price_gold
                profile.save()

            UserDynamicBlessing.objects.create(user=user, blessing=b)
            return JsonResponse({"success": True, "message": f"¡Bendición {b.name} adquirida! Ve a Inicio para farmearla."})

        return JsonResponse({"error": "Tipo inválido."}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@login_required
def farm_dynamic_blessing(request, pk):
    try:
        user_blessing = UserDynamicBlessing.objects.get(pk=pk, user=request.user)
        blessing = user_blessing.blessing

        # Check cooldown
        if user_blessing.last_claim_at:
            time_passed = timezone.now() - user_blessing.last_claim_at
            if time_passed.total_seconds() < blessing.cooldown_hours * 3600:
                horas_restantes = (blessing.cooldown_hours * 3600 - time_passed.total_seconds()) / 3600
                return JsonResponse({"error": f"Aún debes esperar {horas_restantes:.1f} horas."}, status=400)

        if not blessing.reward_mineral and blessing.reward_gold <= 0:
            return JsonResponse({"error": "Esta bendición no tiene recompensa configurada."}, status=400)

        # Give reward
        if blessing.reward_mineral and blessing.reward_mineral_qty > 0:
            um, _ = UserMineral.objects.get_or_create(user=request.user, mineral=blessing.reward_mineral)
            um.amount += blessing.reward_mineral_qty
            um.save()
            
        if blessing.reward_gold > 0:
            profile = request.user.profile
            profile.cosmos_gold += blessing.reward_gold
            profile.save()

        user_blessing.last_claim_at = timezone.now()
        user_blessing.save()

        msgs = []
        if blessing.reward_mineral and blessing.reward_mineral_qty > 0:
            msgs.append(f"{blessing.reward_mineral_qty} {blessing.reward_mineral.name}")
        if blessing.reward_gold > 0:
            msgs.append(f"{blessing.reward_gold} Cosmos Gold")

        recompensa_str = " y ".join(msgs)
        return JsonResponse({"success": True, "message": f"¡Has recolectado {recompensa_str}!"})
    except UserDynamicBlessing.DoesNotExist:
        return JsonResponse({"error": "Bendición no encontrada."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def my_blessings_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_dynamic_blessings = UserDynamicBlessing.objects.filter(user=request.user).select_related('blessing', 'blessing__reward_mineral').order_by('-obtained_at')
    
    now = timezone.now()
    for ub in user_dynamic_blessings:
        if ub.last_claim_at:
            ub.next_claim_at = ub.last_claim_at + timedelta(hours=ub.blessing.cooldown_hours)
            ub.is_ready = now >= ub.next_claim_at
        else:
            ub.is_ready = True
            ub.next_claim_at = None

    return render(request, "game/my_blessings.html", {
        "profile": profile,
        "user_dynamic_blessings": user_dynamic_blessings,
        "now": now
    })
