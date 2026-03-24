from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from .models_packs import StorePack, PackMinerReward, PackToolReward, PackTransportReward
from .models import Mineral, MinerType, ToolType, TransportType, Profile, UserMiner, UserTool, UserTransport
from decimal import Decimal
import random


@ensure_csrf_cookie
@login_required
@user_passes_test(lambda u: u.is_staff)
def packs_admin_view(request):
    import json
    minerals = Mineral.objects.all().order_by('name')
    miners = MinerType.objects.filter(is_active=True).order_by('name')
    tools = ToolType.objects.filter(is_active=True).order_by('name')
    transports = TransportType.objects.filter(is_active=True).order_by('name')
    miners_json = json.dumps([{"id": m.id, "name": m.name} for m in miners])
    tools_json = json.dumps([{"id": t.id, "name": t.name} for t in tools])
    transports_json = json.dumps([{"id": t.id, "name": t.name} for t in transports])
    return render(request, "game/packs_admin.html", {
        "minerals": minerals,
        "miners_json": miners_json,
        "tools_json": tools_json,
        "transports_json": transports_json,
    })


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def packs_list(request):
    items = []
    for p in StorePack.objects.all().order_by("-created_at"):
        miner_rewards = [
            {
                "id": r.id,
                "miner_id": r.miner_id,
                "miner_name": r.miner.name,
                "chance": float(r.chance),
                "probability_label": r.probability_label,
            }
            for r in p.miner_rewards.select_related("miner").all()
        ]
        tool_rewards = [
            {
                "id": r.id,
                "tool_id": r.tool_id,
                "tool_name": r.tool.name,
                "chance": float(r.chance),
                "probability_label": r.probability_label,
            }
            for r in p.tool_rewards.select_related("tool").all()
        ]
        transport_rewards = [
            {
                "id": r.id,
                "transport_id": r.transport_id,
                "transport_name": r.transport.name,
                "chance": float(r.chance),
                "probability_label": r.probability_label,
            }
            for r in p.transport_rewards.select_related("transport").all()
        ]
        items.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price_gold": float(p.price_gold),
            "purchase_mineral_id": p.purchase_mineral_id,
            "purchase_mineral_name": p.purchase_mineral.name if p.purchase_mineral else None,
            "purchase_mineral_qty": p.purchase_mineral_qty,
            "external_link": p.external_link or "",
            "is_active": p.is_active,
            "miner_rewards": miner_rewards,
            "tool_rewards": tool_rewards,
            "transport_rewards": transport_rewards,
        })
    return JsonResponse({"success": True, "items": items})


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def pack_create(request):
    try:
        with transaction.atomic():
            pack = _save_pack_from_request(request, None)
        return JsonResponse({"success": True, "id": pack.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def pack_update(request, pk):
    try:
        pack = StorePack.objects.get(pk=pk)
        with transaction.atomic():
            _save_pack_from_request(request, pack)
        return JsonResponse({"success": True})
    except StorePack.DoesNotExist:
        return JsonResponse({"error": "Paquete no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def pack_toggle(request, pk):
    try:
        p = StorePack.objects.get(pk=pk)
        p.is_active = not p.is_active
        p.save()
        return JsonResponse({"success": True, "is_active": p.is_active})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def pack_delete(request, pk):
    try:
        StorePack.objects.get(pk=pk).delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def _save_pack_from_request(request, pack):
    data = request.POST
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("El nombre del paquete es requerido")

    mineral_id = data.get("purchase_mineral_id") or None
    mineral = Mineral.objects.get(pk=mineral_id) if mineral_id else None

    if pack is None:
        pack = StorePack()

    pack.name = name
    pack.description = data.get("description", "")
    pack.price_gold = Decimal(data.get("price_gold") or "0")
    pack.purchase_mineral = mineral
    pack.purchase_mineral_qty = int(data.get("purchase_mineral_qty") or 0)
    pack.external_link = data.get("external_link") or None
    pack.is_active = data.get("is_active") in ["1", "true", "on", "True"]
    if "image" in request.FILES:
        pack.image = request.FILES["image"]
    pack.save()

    # Clear old rewards and re-apply
    pack.miner_rewards.all().delete()
    pack.tool_rewards.all().delete()

    # Miner rewards (expected keys: miner_id[], miner_chance[], miner_label[])
    miner_ids = data.getlist("miner_id[]")
    miner_chances = data.getlist("miner_chance[]")
    miner_labels = data.getlist("miner_label[]")
    for mid, chance, label in zip(miner_ids, miner_chances, miner_labels):
        if mid and chance:
            PackMinerReward.objects.create(
                pack=pack,
                miner_id=int(mid),
                chance=Decimal(chance),
                probability_label=label
            )

    # Tool rewards
    tool_ids = data.getlist("tool_id[]")
    tool_chances = data.getlist("tool_chance[]")
    tool_labels = data.getlist("tool_label[]")
    for tid, chance, label in zip(tool_ids, tool_chances, tool_labels):
        if tid and chance:
            PackToolReward.objects.create(
                pack=pack,
                tool_id=int(tid),
                chance=Decimal(chance),
                probability_label=label
            )

    # Transport rewards
    transport_ids = data.getlist("transport_id[]")
    transport_chances = data.getlist("transport_chance[]")
    transport_labels = data.getlist("transport_label[]")
    for tid, chance, label in zip(transport_ids, transport_chances, transport_labels):
        if tid and chance:
            PackTransportReward.objects.create(
                pack=pack,
                transport_id=int(tid),
                chance=Decimal(chance),
                probability_label=label
            )

    return pack


# Public view
@ensure_csrf_cookie
@login_required
def packs_public_view(request):
    packs = StorePack.objects.filter(is_active=True).prefetch_related(
        "miner_rewards__miner", "tool_rewards__tool", "transport_rewards__transport"
    ).order_by("-created_at")
    return render(request, "game/packs_public.html", {"packs": packs})


@require_POST
@csrf_protect
@login_required
def buy_pack(request, pk):
    try:
        pack = StorePack.objects.get(pk=pk, is_active=True)

        # If external link, this endpoint shouldn't be called — but guard anyway
        if pack.external_link:
            return JsonResponse({"error": "Este paquete usa enlace externo"}, status=400)

        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(user=request.user)

            # Deduct payment
            if pack.purchase_mineral and pack.purchase_mineral_qty > 0:
                from .models import UserMineral
                um = UserMineral.objects.select_for_update().filter(
                    user=request.user, mineral=pack.purchase_mineral
                ).first()
                if not um or um.amount < pack.purchase_mineral_qty:
                    return JsonResponse({
                        "error": f"No tienes suficiente {pack.purchase_mineral.name}."
                    }, status=400)
                um.amount -= pack.purchase_mineral_qty
                um.save()
            else:
                if profile.cosmos_gold < pack.price_gold:
                    return JsonResponse({"error": "No tienes suficiente Cosmos Gold."}, status=400)
                profile.cosmos_gold -= pack.price_gold
                profile.save()

            rewards = []

            # Draw miner reward (if any configured)
            miner_pool = list(pack.miner_rewards.select_related("miner").all())
            if miner_pool:
                drawn_miner = _draw(miner_pool)
                if drawn_miner:
                    UserMiner.objects.create(owner=profile, miner_type=drawn_miner.miner)
                    rewards.append({"type": "miner", "name": drawn_miner.miner.name})

            # Draw tool reward (if any configured)
            tool_pool = list(pack.tool_rewards.select_related("tool").all())
            if tool_pool:
                drawn_tool = _draw(tool_pool)
                if drawn_tool:
                    UserTool.objects.create(owner=profile, tool_type=drawn_tool.tool)
                    rewards.append({"type": "tool", "name": drawn_tool.tool.name})

            # Draw transport reward (if any configured)
            transport_pool = list(pack.transport_rewards.select_related("transport").all())
            if transport_pool:
                drawn_transport = _draw(transport_pool)
                if drawn_transport:
                    UserTransport.objects.create(owner=profile, transport_type=drawn_transport.transport)
                    rewards.append({"type": "transport", "name": drawn_transport.transport.name})

        return JsonResponse({"success": True, "rewards": rewards})

    except StorePack.DoesNotExist:
        return JsonResponse({"error": "Paquete no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def _draw(pool):
    """Weighted random draw from a list of reward objects that have .chance."""
    rand = random.random()
    cumulative = 0.0
    for item in pool:
        cumulative += float(item.chance)
        if rand <= cumulative:
            return item
    return pool[-1]  # fallback to last if floating point rounding
