import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

from .models_gifts import AllianceGift, AllianceGiftAssignment, AllianceGiftWinner
from .models_alliances import Alliance
from .models_planets import Mineral, UserMineral
from .models import Profile, MinerType, UserMiner, ToolType, UserTool, TransportType, UserTransport


# ═══════════════════════════════════════════
# ADMIN: Gift Management
# ═══════════════════════════════════════════

@login_required
def gifts_admin(request):
    """Admin page to manage gift templates and assign them to alliances."""
    if not request.user.is_staff:
        return redirect('home')

    gifts = AllianceGift.objects.all().order_by('-created_at')
    alliances = Alliance.objects.all().order_by('name')
    minerals = Mineral.objects.all()
    miner_types = MinerType.objects.filter(is_active=True)
    tool_types = ToolType.objects.filter(is_active=True)
    transport_types = TransportType.objects.filter(is_active=True)

    # Recent assignments
    assignments = AllianceGiftAssignment.objects.select_related(
        'gift', 'alliance', 'winner_record__winner'
    ).order_by('-assigned_at')[:30]

    return render(request, 'game/gifts_admin.html', {
        'gifts': gifts,
        'alliances': alliances,
        'minerals': minerals,
        'miner_types': miner_types,
        'tool_types': tool_types,
        'transport_types': transport_types,
        'assignments': assignments,
    })


@require_POST
@login_required
@csrf_protect
def gift_create(request):
    """Create a new gift template."""
    if not request.user.is_staff:
        return JsonResponse({"error": "No autorizado"}, status=403)

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    gold_amount = int(request.POST.get('gold_amount', 0) or 0)
    mineral_id = request.POST.get('mineral_id') or None
    mineral_quantity = int(request.POST.get('mineral_quantity', 0) or 0)
    miner_type_id = request.POST.get('miner_type_id') or None
    tool_type_id = request.POST.get('tool_type_id') or None
    transport_type_id = request.POST.get('transport_type_id') or None
    image = request.FILES.get('image')

    if not name:
        return JsonResponse({"error": "El nombre es obligatorio."}, status=400)

    gift = AllianceGift.objects.create(
        name=name,
        description=description,
        gold_amount=gold_amount,
        mineral_id=mineral_id if mineral_id else None,
        mineral_quantity=mineral_quantity,
        miner_type_id=miner_type_id if miner_type_id else None,
        tool_type_id=tool_type_id if tool_type_id else None,
        transport_type_id=transport_type_id if transport_type_id else None,
        image=image,
    )

    return JsonResponse({"success": True, "message": f"Regalo '{gift.name}' creado."})


@require_POST
@login_required
@csrf_protect
def gift_delete(request, gift_id):
    """Delete a gift template."""
    if not request.user.is_staff:
        return JsonResponse({"error": "No autorizado"}, status=403)

    gift = get_object_or_404(AllianceGift, id=gift_id)
    gift.delete()
    return JsonResponse({"success": True, "message": "Regalo eliminado."})


@require_POST
@login_required
@csrf_protect
def gift_assign(request):
    """Assign a gift to an alliance."""
    if not request.user.is_staff:
        return JsonResponse({"error": "No autorizado"}, status=403)

    gift_id = request.POST.get('gift_id')
    alliance_id = request.POST.get('alliance_id')

    gift = get_object_or_404(AllianceGift, id=gift_id)
    alliance = get_object_or_404(Alliance, id=alliance_id)

    AllianceGiftAssignment.objects.create(gift=gift, alliance=alliance)
    return JsonResponse({"success": True, "message": f"'{gift.name}' asignado a {alliance.name}."})


# ═══════════════════════════════════════════
# MEMBER: Gift Raffle / Claims
# ═══════════════════════════════════════════

@login_required
def alliance_gifts_page(request):
    """Page where the alliance leader can see and raffle gifts."""
    profile = request.user.profile
    if not profile.alliance:
        messages.error(request, "No perteneces a una alianza.")
        return redirect('alliances_view')

    alliance = profile.alliance
    
    # Available (not yet raffled) gifts — only leader can see/raffle these
    available = []
    is_leader = (alliance.leader == request.user)
    if is_leader:
        available = AllianceGiftAssignment.objects.filter(
            alliance=alliance, is_raffled=False
        ).select_related('gift__mineral', 'gift__miner_type', 'gift__tool_type', 'gift__transport_type')

    # All wins in this alliance
    history = AllianceGiftWinner.objects.filter(
        assignment__alliance=alliance
    ).select_related('assignment__gift', 'winner').order_by('-won_at')[:30]

    # User's own pending gifts to claim
    my_pending = AllianceGiftWinner.objects.filter(
        winner=request.user, is_claimed=False
    ).select_related('assignment__gift')

    return render(request, 'game/alliance_gifts.html', {
        'alliance': alliance,
        'is_leader': is_leader,
        'available': available,
        'history': history,
        'my_pending': my_pending,
    })


@require_POST
@login_required
@csrf_protect
def alliance_raffle_gift(request, assignment_id):
    """Raffle a gift among alliance members. DOES NOT deliver items yet."""
    profile = request.user.profile
    if not profile.alliance:
        return JsonResponse({"error": "No perteneces a una alianza."}, status=403)

    alliance = profile.alliance
    if alliance.leader != request.user:
        return JsonResponse({"error": "Solo el líder puede sortear regalos."}, status=403)

    assignment = get_object_or_404(AllianceGiftAssignment, id=assignment_id, alliance=alliance)
    if assignment.is_raffled:
        return JsonResponse({"error": "Este regalo ya fue sorteado."}, status=400)

    # Get all alliance members
    members = Profile.objects.filter(alliance=alliance).select_related('user')
    if not members.exists():
        return JsonResponse({"error": "No hay miembros en la alianza."}, status=400)

    # Pick random winner
    winner_profile = random.choice(list(members))
    winner_user = winner_profile.user
    gift = assignment.gift

    # Mark as raffled and record winner (But don't deliver contents yet)
    assignment.is_raffled = True
    assignment.save()

    AllianceGiftWinner.objects.create(assignment=assignment, winner=winner_user, is_claimed=False)

    return JsonResponse({
        "success": True,
        "winner": winner_user.username,
        "gift_name": gift.name,
        "gift_image": gift.image.url if gift.image else None,
    })


@require_POST
@login_required
@csrf_protect
def alliance_claim_gift(request, win_id):
    """Deliver a won gift to the user."""
    win = get_object_or_404(AllianceGiftWinner, id=win_id, winner=request.user)
    
    if win.is_claimed:
        return JsonResponse({"error": "Este regalo ya fue reclamado."}, status=400)

    profile = request.user.profile
    gift = win.assignment.gift
    delivery_items = []

    # Deliver items
    if gift.gold_amount > 0:
        profile.cosmos_gold += gift.gold_amount
        profile.save()
        delivery_items.append({"name": "Cosmos Gold", "amount": gift.gold_amount, "type": "gold"})

    if gift.mineral and gift.mineral_quantity > 0:
        um, _ = UserMineral.objects.get_or_create(user=request.user, mineral=gift.mineral, defaults={'amount':0})
        um.amount += gift.mineral_quantity
        um.save()
        delivery_items.append({"name": gift.mineral.name, "amount": gift.mineral_quantity, "type": "mineral"})

    if gift.miner_type:
        UserMiner.objects.create(owner=profile, miner_type=gift.miner_type)
        delivery_items.append({"name": gift.miner_type.name, "type": "miner", "image": gift.miner_type.image.url if gift.miner_type.image else None})

    if gift.tool_type:
        UserTool.objects.create(owner=profile, tool_type=gift.tool_type)
        delivery_items.append({"name": gift.tool_type.name, "type": "tool", "image": gift.tool_type.image.url if gift.tool_type.image else None})

    if gift.transport_type:
        UserTransport.objects.create(owner=profile, transport_type=gift.transport_type)
        delivery_items.append({"name": gift.transport_type.name, "type": "transport", "image": gift.transport_type.image.url if gift.transport_type.image else None})

    # Mark as claimed
    win.is_claimed = True
    win.save()

    return JsonResponse({
        "success": True,
        "gift_name": gift.name,
        "gift_image": gift.image.url if gift.image else None,
        "items": delivery_items
    })
