import json
import random
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.files.base import ContentFile
from django.contrib import messages
from .models import Profile
from .models_planets import Planet, UserMineral
from .models_alliances import Alliance, AllianceRequest, AllianceGlobalConfig, AlliancePlanet
from PIL import Image
from .models_gifts import AllianceGiftWinner
import io

@login_required
def alliances_view(request):
    profile = request.user.profile
    
    # Check if user is in an alliance
    if profile.alliance:
        # If in alliance, show my alliance panel
        alliance = profile.alliance
        members = alliance.members_profiles.select_related('user').all()
        pending_requests = []
        if alliance.leader == request.user or alliance.right_hand == request.user:
            pending_requests = alliance.requests.filter(status='pending').select_related('user')
            
        # Gifts pending count
        my_pending_gifts_count = AllianceGiftWinner.objects.filter(winner=request.user, is_claimed=False).count()
            
        return render(request, "game/alliance_my.html", {
            "profile": profile,
            "alliance": alliance,
            "members": members,
            "pending_requests": pending_requests,
            "is_leader": alliance.leader == request.user,
            "is_right_hand": alliance.right_hand == request.user,
            "is_captain": alliance.captain == request.user,
            "my_pending_gifts_count": my_pending_gifts_count,
        })
    else:
        # If not, show list of alliances to join/create
        alliances = Alliance.objects.all().order_by('-created_at')
        
        # Check cooldown
        cooldown_msg = None
        if profile.alliance_cooldown_until and profile.alliance_cooldown_until > timezone.now():
            diff = profile.alliance_cooldown_until - timezone.now()
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            cooldown_msg = f"Debes esperar {hours}h {minutes}m para unirte a otra alianza."

        return render(request, "game/alliances_list.html", {
            "profile": profile,
            "alliances": alliances,
            "cooldown_msg": cooldown_msg,
        })

@require_POST
@login_required
@csrf_protect
def create_alliance(request):
    profile = request.user.profile
    if profile.alliance:
        return JsonResponse({"error": "Ya perteneces a una alianza."}, status=400)
    
    # Check cooldown
    if profile.alliance_cooldown_until and profile.alliance_cooldown_until > timezone.now():
        return JsonResponse({"error": "Estás bajo cooldown de 24h."}, status=400)

    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    image_file = request.FILES.get("image")

    if not name or len(name) < 3:
        return JsonResponse({"error": "Nombre demasiado corto (min 3 chars)."}, status=400)
    
    if Alliance.objects.filter(name__iexact=name).exists():
        return JsonResponse({"error": f"La alianza '{name}' ya existe."}, status=400)

    # Process image if exists
    processed_image = None
    if image_file:
        if image_file.size > 2 * 1024 * 1024: # 2MB Limit
             return JsonResponse({"error": "La imagen es muy pesada (max 2MB)."}, status=400)
        
        try:
            img = Image.open(io.BytesIO(image_file.read()))
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Reduce quality/resize if too big
            img.thumbnail((400, 400)) # Max 400x400
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=70)
            output.seek(0)
            processed_image = ContentFile(output.read(), name=f"alliance_{timezone.now().timestamp()}.jpg")
        except Exception as e:
            # If gif or error, keep original if small enough
            image_file.seek(0)
            processed_image = image_file

    with transaction.atomic():
        config = AllianceGlobalConfig.get_config()
        alliance = Alliance.objects.create(
            name=name,
            description=description,
            leader=request.user,
            image=processed_image,
            max_members=config.default_max_members
        )
        profile.alliance = alliance
        profile.save()

    return JsonResponse({"success": True})

@require_POST
@login_required
@csrf_protect
def request_join_alliance(request, alliance_id):
    profile = request.user.profile
    if profile.alliance:
        return JsonResponse({"error": "Ya perteneces a una alianza."}, status=400)
    
    if profile.alliance_cooldown_until and profile.alliance_cooldown_until > timezone.now():
        return JsonResponse({"error": "Bajo cooldown de 24h."}, status=400)

    alliance = get_object_or_404(Alliance, id=alliance_id)
    
    # Check if already max members
    if alliance.members_profiles.count() >= alliance.max_members:
        return JsonResponse({"error": "La alianza está llena."}, status=400)

    # If already exists (maybe rejected), update it back to pending
    AllianceRequest.objects.update_or_create(
        user=request.user, 
        alliance=alliance, 
        defaults={'status': 'pending'}
    )
    return JsonResponse({"success": True, "message": "Solicitud enviada."})

@require_POST
@login_required
@csrf_protect
def handle_request(request, request_id):
    # Action: accept or reject
    action = request.POST.get("action")
    alliance_request = get_object_or_404(AllianceRequest, id=request_id)
    alliance = alliance_request.alliance

    # Permissions
    if alliance.leader != request.user and alliance.right_hand != request.user:
        return JsonResponse({"error": "No tienes permisos."}, status=403)

    if alliance_request.status != 'pending':
        return JsonResponse({"error": "Esta solicitud ya fue procesada."}, status=400)

    if action == "accept":
        # Check if alliance is full
        if alliance.members_profiles.count() >= alliance.max_members:
            return JsonResponse({"error": "La alianza está llena."}, status=400)
        
        with transaction.atomic():
            target_profile = alliance_request.user.profile
            # Check if user already joined another alliance in the meantime
            if target_profile.alliance:
                alliance_request.status = 'rejected'
                alliance_request.save()
                return JsonResponse({"error": "El usuario ya pertenece a otra alianza."}, status=400)

            # Accept
            alliance_request.status = 'accepted'
            alliance_request.save()
            target_profile.alliance = alliance
            target_profile.save()
            
            # Delete/Reject other pending requests of this user
            AllianceRequest.objects.filter(user=alliance_request.user, status='pending').exclude(id=request_id).update(status='rejected')
            
        return JsonResponse({"success": True, "message": "Usuario aceptado."})
    
    elif action == "reject":
        alliance_request.status = 'rejected'
        alliance_request.save()
        return JsonResponse({"success": True, "message": "Solicitud rechazada."})

    return JsonResponse({"error": "Acción inválida."}, status=400)

@require_POST
@login_required
@csrf_protect
def leave_alliance(request):
    profile = request.user.profile
    alliance = profile.alliance
    if not alliance:
        return JsonResponse({"error": "No perteneces a una alianza."}, status=400)

    user = request.user
    with transaction.atomic():
        members_count = alliance.members_profiles.count()
        
        if alliance.leader == user:
            if members_count == 1:
                # Alone? Delete alliance
                alliance.delete()
                # No cooldown if deleting? User said: "si esta solo puede simplemente abandonar... no le saldra abandonar sino eliminar"
                # Actually user typically wants to be free. Let's set the cooldown regardless of leader/member to prevent abuse.
                profile.alliance = None
                profile.alliance_cooldown_until = timezone.now() + timedelta(hours=24)
                profile.save()
                return JsonResponse({"success": True, "message": "Alianza eliminada."})
            else:
                # Succession logic
                # 1. Mano Derecha
                if alliance.right_hand and alliance.right_hand != user:
                    alliance.leader = alliance.right_hand
                    alliance.right_hand = None
                else:
                    # 2. Random member
                    other_members = alliance.members_profiles.exclude(user=user)
                    new_leader_profile = random.choice(list(other_members))
                    alliance.leader = new_leader_profile.user
                alliance.save()

        # Regular leave or leader who gave away power
        profile.alliance = None
        profile.alliance_cooldown_until = timezone.now() + timedelta(hours=24)
        profile.save()

    return JsonResponse({"success": True, "message": "Has abandonado la alianza."})

@require_POST
@login_required
@csrf_protect
def nominate_right_hand(request, target_user_id):
    profile = request.user.profile
    alliance = profile.alliance
    if not alliance or alliance.leader != request.user:
        return JsonResponse({"error": "Solo el líder puede nombrar mano derecha."}, status=403)

    target_user = get_object_or_404(User, id=target_user_id)
    if target_user.profile.alliance != alliance:
        return JsonResponse({"error": "El usuario no pertenece a tu alianza."}, status=400)
    
    if target_user == request.user:
        return JsonResponse({"error": "No puedes ser tu propia mano derecha."}, status=400)

    alliance.right_hand = target_user
    alliance.save()
    return JsonResponse({"success": True, "message": f"{target_user.username} es ahora la mano derecha."})

@require_POST
@login_required
@csrf_protect
def nominate_captain(request, target_user_id):
    profile = request.user.profile
    alliance = profile.alliance
    if not alliance or alliance.leader != request.user:
        return JsonResponse({"error": "Solo el líder puede nombrar capitán."}, status=403)

    target_user = get_object_or_404(User, id=target_user_id)
    if target_user.profile.alliance != alliance:
        return JsonResponse({"error": "El usuario no pertenece a tu alianza."}, status=400)
    
    if target_user == request.user:
        return JsonResponse({"error": "No puedes nombrarte a ti mismo."}, status=400)

    alliance.captain = target_user
    alliance.save()
    return JsonResponse({"success": True, "message": f"{target_user.username} es ahora el capitán."})

@require_POST
@login_required
@csrf_protect
def expel_member(request, target_user_id):
    profile = request.user.profile
    alliance = profile.alliance
    if not alliance or alliance.leader != request.user:
        return JsonResponse({"error": "Solo el líder puede expulsar miembros."}, status=403)

    target_user = get_object_or_404(User, id=target_user_id)
    if target_user == request.user:
        return JsonResponse({"error": "No puedes expulsarte a ti mismo."}, status=400)

    target_profile = target_user.profile
    if target_profile.alliance != alliance:
        return JsonResponse({"error": "El usuario no pertenece a tu alianza."}, status=400)

    with transaction.atomic():
        if alliance.right_hand == target_user:
            alliance.right_hand = None
            alliance.save()
            
        target_profile.alliance = None
        # Expelled users also get cooldown? Use usually yes to prevent jumping.
        target_profile.alliance_cooldown_until = timezone.now() + timedelta(hours=24)
        target_profile.save()

    return JsonResponse({"success": True, "message": "Miembro expulsado."})

@login_required
@user_passes_test(lambda u: u.is_staff)
def alliance_admin_dashboard(request):
    alliances = Alliance.objects.all().order_by('-created_at')
    config = AllianceGlobalConfig.get_config()
    return render(request, "game/alliances_admin.html", {
        "alliances": alliances,
        "config": config
    })

@require_POST
@login_required
@csrf_protect
@user_passes_test(lambda u: u.is_staff)
def alliance_admin_global_update(request):
    max_members = request.POST.get("default_max_members")
    if max_members:
        config = AllianceGlobalConfig.get_config()
        config.default_max_members = int(max_members)
        config.save()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Dato inválido."}, status=400)


@require_POST
@login_required
@csrf_protect
@user_passes_test(lambda u: u.is_staff)
def alliance_admin_update(request, alliance_id):
    alliance = get_object_or_404(Alliance, id=alliance_id)
    
    name = request.POST.get("name")
    description = request.POST.get("description")
    max_members = request.POST.get("max_members")
    image_file = request.FILES.get("image")

    if name:
        alliance.name = name
    if description is not None:
        alliance.description = description
    if max_members:
        alliance.max_members = int(max_members)
    
    if image_file:
         # Simplified update (can reuse compression logic if needed)
         alliance.image = image_file

    alliance.save()
    return JsonResponse({"success": True})

@login_required
def alliance_planets_list(request):
    """View for every member to see their alliance's conquered worlds."""
    profile = request.user.profile
    if not profile.alliance:
        messages.error(request, "Debes pertenecer a una alianza.")
        return redirect('alliances_view')
    
    alliance = profile.alliance
    
    # Get only planets already owned by THIS alliance
    owned_alliance_planets = AlliancePlanet.objects.filter(alliance=alliance).select_related('planet')
    
    return render(request, 'game/alliance_planets_list.html', {
        'alliance_planets': owned_alliance_planets,
        'alliance': alliance,
    })

@login_required
def alliance_planets_store(request):
    """View only for leader/right-hand to buy new worlds."""
    profile = request.user.profile
    if not profile.alliance:
        messages.error(request, "Debes pertenecer a una alianza.")
        return redirect('alliances_view')
    
    alliance = profile.alliance
    if alliance.leader != request.user and alliance.right_hand != request.user and alliance.captain != request.user:
        messages.error(request, "Solo el Líder, Mano Derecha o Capitán pueden acceder a la tesorería de planetas.")
        return redirect('alliances_view')
    
    is_privileged = True
    
    # Get all planets that are for alliances
    all_alliance_planets = Planet.objects.filter(is_alliance=True, is_active=True)
    
    # Get IDs of planets already owned by THIS alliance
    owned_ids = set(AlliancePlanet.objects.filter(alliance=alliance).values_list('planet_id', flat=True))
    
    # Tag planets as owned or not
    for p in all_alliance_planets:
        p.is_owned = p.id in owned_ids
    
    return render(request, 'game/alliance_planets_store.html', {
        'planets': all_alliance_planets,
        'is_privileged': is_privileged,
        'alliance': alliance,
    })

@require_POST
@login_required
@csrf_protect
def alliance_buy_planet(request, planet_id):
    profile = request.user.profile
    if not profile.alliance:
        return JsonResponse({"error": "No perteneces a una alianza."}, status=403)
    
    alliance = profile.alliance
    if alliance.leader != request.user and alliance.right_hand != request.user and alliance.captain != request.user:
        return JsonResponse({"error": "No tienes permisos de mando."}, status=403)
    
    planet = get_object_or_404(Planet, id=planet_id, is_alliance=True)
    
    # Check if already owned
    if AlliancePlanet.objects.filter(alliance=alliance, planet=planet).exists():
        return JsonResponse({"error": "La alianza ya posee este planeta."}, status=400)
    
    # Check price
    # Case 1: Mineral Price set
    if planet.price_mineral:
        user_mineral = UserMineral.objects.filter(user=request.user, mineral=planet.price_mineral).first()
        if not user_mineral or user_mineral.amount < planet.price_mineral_quantity:
            return JsonResponse({"error": f"No tienes suficiente {planet.price_mineral.name}. Necesitas {planet.price_mineral_quantity}."}, status=400)
        
        # Deduct mineral
        with transaction.atomic():
            user_mineral.amount -= planet.price_mineral_quantity
            user_mineral.save()
            AlliancePlanet.objects.get_or_create(alliance=alliance, planet=planet)
            
    # Case 2: Gold Price set
    elif planet.price_gold > 0:
        if profile.cosmos_gold < planet.price_gold:
            return JsonResponse({"error": "No tienes suficiente Cosmos Gold."}, status=400)
            
        with transaction.atomic():
            profile.cosmos_gold -= planet.price_gold
            profile.save()
            AlliancePlanet.objects.get_or_create(alliance=alliance, planet=planet)
            
    # Case 3: Free (but marked is_alliance)
    else:
        AlliancePlanet.objects.get_or_create(alliance=alliance, planet=planet)
    
    return JsonResponse({"success": True, "message": f"¡{planet.name} ha sido anexado a los dominios de {alliance.name}!"})

@require_POST
@login_required
@csrf_protect
@user_passes_test(lambda u: u.is_staff)
def alliance_admin_reset_cooldowns(request):
    Profile.objects.all().update(alliance_cooldown_until=None)
    return JsonResponse({"success": True, "message": "Todos los cooldowns han sido reiniciados."})
