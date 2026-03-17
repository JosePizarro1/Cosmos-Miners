from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models import (
    Season, UserSeasonEntry, SeasonLevel, 
    SeasonLevelRequirement, SeasonLevelReward,
    MinerType, TransportType, ToolType
)
import json
from django.db import transaction

@login_required
@user_passes_test(lambda u: u.is_staff)
def seasons_admin_view(request):
    return render(request, "game/seasons_admin.html")

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def seasons_list(request):
    seasons = Season.objects.all().order_by('-start_date')
    items = []
    for s in seasons:
        items.append({
            "id": s.id,
            "name": s.name,
            "start_date": s.start_date.isoformat(),
            "end_date": s.end_date.isoformat(),
            "claim_rewards_at": s.claim_rewards_at.isoformat(),
            "is_active_override": s.is_active_override,
            "status": s.status
        })
    return JsonResponse({"items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def season_create(request):
    try:
        data = json.loads(request.body)
        Season.objects.create(
            name=data['name'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            claim_rewards_at=data['claim_rewards_at'],
            is_active_override=data.get('is_active_override', False)
        )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def season_update(request, pk):
    try:
        season = get_object_or_404(Season, pk=pk)
        data = json.loads(request.body)
        season.name = data['name']
        season.start_date = data['start_date']
        season.end_date = data['end_date']
        season.claim_rewards_at = data['claim_rewards_at']
        season.is_active_override = data.get('is_active_override', False)
        season.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def season_delete(request, pk):
    try:
        season = get_object_or_404(Season, pk=pk)
        season.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def season_toggle_override(request, pk):
    try:
        season = get_object_or_404(Season, pk=pk)
        # If we are activating this one, we deactivate others to avoid confusion? 
        # Actually user might want multiple, but let's just toggle this one.
        season.is_active_override = not season.is_active_override
        season.save()
        return JsonResponse({"success": True, "new_state": season.is_active_override})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
@login_required
def public_rankings_list(request):
    seasons = Season.objects.all().order_by('-start_date')
    data = []
    now = timezone.now()
    
    # Pre-fetch user entries for these seasons
    user_entries = {entry.season_id: entry for entry in UserSeasonEntry.objects.filter(user=request.user, season__in=seasons)}
    
    for s in seasons:
        entry = user_entries.get(s.id)
        data.append({
            "id": s.id,
            "name": s.name,
            "start_date": s.start_date.isoformat(),
            "end_date": s.end_date.isoformat(),
            "claim_rewards_at": s.claim_rewards_at.isoformat(),
            "status": s.status,
            "user_entry": {
                "level_name": entry.level.name,
                "locked_until": entry.locked_until.isoformat(),
                "is_locked": entry.locked_until > now,
                "rewards": [{
                    "type": r_item.reward_type,
                    "amount": str(r_item.amount),
                    "name": r_item.miner_type.name if r_item.miner_type else (r_item.transport_type.name if r_item.transport_type else (r_item.tool_type.name if r_item.tool_type else "Cosmogold"))
                } for r_item in entry.level.rewards.all()]
            } if entry else None
        })
    return JsonResponse({"items": data})

@login_required
def get_levels_api(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    levels = season.levels.all().order_by('name')
    data = []
    for l in levels:
        reqs = []
        for r in l.requirements.all():
            reqs.append({
                "type": r.requirement_type,
                "type_display": r.get_requirement_type_display(),
                "value": str(r.value)
            })
        rewards = []
        for r_item in l.rewards.all():
            rewards.append({
                "type": r_item.reward_type,
                "amount": str(r_item.amount),
                "name": r_item.miner_type.name if r_item.miner_type else (r_item.transport_type.name if r_item.transport_type else (r_item.tool_type.name if r_item.tool_type else "Cosmogold"))
            })
        data.append({
            "id": l.id,
            "name": l.name,
            "lock_duration_days": l.lock_duration_days,
            "requirements": reqs,
            "rewards": rewards
        })
    return JsonResponse({"items": data})

@login_required
def get_available_items_api(request):
    # Returns items NOT currently locked in any season
    now = timezone.now()
    locked_entries = UserSeasonEntry.objects.filter(user=request.user, locked_until__gt=now)
    
    locked_miners = set(locked_entries.values_list('miner_used_id', flat=True))
    locked_transports = set(locked_entries.values_list('transport_used_id', flat=True))
    locked_tools = set(locked_entries.values_list('tool_used_id', flat=True))
    
    from .models import UserMiner, UserTransport, UserTool
    
    miners = UserMiner.objects.filter(owner__user=request.user).exclude(id__in=locked_miners)
    transports = UserTransport.objects.filter(owner__user=request.user).exclude(id__in=locked_transports)
    tools = UserTool.objects.filter(owner__user=request.user).exclude(id__in=locked_tools)
    
    return JsonResponse({
        "miners": [{"id": m.id, "name": m.miner_type.name, "attempts": m.miner_type.attempts, "image": m.miner_type.image.url if m.miner_type.image else None} for m in miners],
        "transports": [{"id": t.id, "name": t.transport_type.name, "speed": t.transport_type.speed, "image": t.transport_type.image.url if t.transport_type.image else None} for t in transports],
        "tools": [{"id": t.id, "name": t.tool_type.name, "multiplier": str(t.tool_type.production_multiplier), "image": t.tool_type.image.url if t.tool_type.image else None} for t in tools],
    })

@require_POST
@csrf_protect
@login_required
def enter_level_api(request):
    try:
        data = json.loads(request.body)
        level_id = data.get('level_id')
        miner_id = data.get('miner_id')
        transport_id = data.get('transport_id')
        tool_id = data.get('tool_id')
        
        level = get_object_or_404(SeasonLevel, pk=level_id)
        
        if level.season.status != 'active':
            return JsonResponse({"error": "La temporada no está activa"}, status=400)
            
        if UserSeasonEntry.objects.filter(user=request.user, season=level.season).exists():
            return JsonResponse({"error": "Ya has ingresado a un nivel en esta temporada"}, status=400)
            
        from .models import UserMiner, UserTransport, UserTool
        
        miner = UserMiner.objects.filter(pk=miner_id, owner__user=request.user).first() if miner_id else None
        transport = UserTransport.objects.filter(pk=transport_id, owner__user=request.user).first() if transport_id else None
        tool = UserTool.objects.filter(pk=tool_id, owner__user=request.user).first() if tool_id else None

        # Dynamic requirements validation
        for r in level.requirements.all():
            if r.requirement_type == 'miner_attempts':
                if not miner: return JsonResponse({"error": "Se requiere un minero para este nivel"}, status=400)
                if miner.miner_type.attempts < r.value:
                    return JsonResponse({"error": f"El minero debe tener al menos {r.value} intentos"}, status=400)
            
            if r.requirement_type == 'transport_speed':
                if not transport: return JsonResponse({"error": "Se requiere un transporte para este nivel"}, status=400)
                if transport.transport_type.speed < r.value:
                    return JsonResponse({"error": f"El transporte debe tener al menos {r.value}% de velocidad"}, status=400)
            
            if r.requirement_type == 'tool_multiplier':
                if not tool: return JsonResponse({"error": "Se requiere una herramienta para este nivel"}, status=400)
                if tool.tool_type.production_multiplier < r.value:
                    return JsonResponse({"error": f"La herramienta debe tener al menos {r.value} de multiplicador"}, status=400)

        now = timezone.now()
        locked_q = UserSeasonEntry.objects.filter(user=request.user, locked_until__gt=now)
        if miner and locked_q.filter(miner_used=miner).exists():
            return JsonResponse({"error": "El minero seleccionado está inhabilitado"}, status=400)
        if transport and locked_q.filter(transport_used=transport).exists():
            return JsonResponse({"error": "El transporte seleccionado está inhabilitado"}, status=400)
        if tool and locked_q.filter(tool_used=tool).exists():
            return JsonResponse({"error": "La herramienta seleccionada está inhabilitada"}, status=400)

        with transaction.atomic():
            UserSeasonEntry.objects.create(
                user=request.user,
                season=level.season,
                level=level,
                miner_used=miner,
                transport_used=transport,
                tool_used=tool,
                locked_until=now + timezone.timedelta(days=level.lock_duration_days)
            )
            
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def season_levels_admin_list(request, season_id):
    levels = SeasonLevel.objects.filter(season_id=season_id).order_by('name')
    items = []
    for l in levels:
        reqs = []
        for r in l.requirements.all():
            reqs.append({
                "type": r.requirement_type,
                "value": str(r.value)
            })
        rewards = []
        for r_item in l.rewards.all():
            rewards.append({
                "type": r_item.reward_type,
                "amount": str(r_item.amount),
                "item_id": r_item.miner_type_id or r_item.transport_type_id or r_item.tool_type_id
            })
        items.append({
            "id": l.id,
            "name": l.name,
            "lock_duration_days": l.lock_duration_days,
            "requirements": reqs,
            "rewards": rewards
        })
    return JsonResponse({"items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def level_create(request):
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            lvl = SeasonLevel.objects.create(
                season_id=data['season_id'],
                name=data['name'],
                lock_duration_days=data.get('lock_duration_days', 7)
            )
            requirements = data.get('requirements', [])
            for r in requirements:
                SeasonLevelRequirement.objects.create(
                    level=lvl,
                    requirement_type=r['type'],
                    value=r['value']
                )
            rewards = data.get('rewards', [])
            for rw in rewards:
                SeasonLevelReward.objects.create(
                    level=lvl,
                    reward_type=rw['type'],
                    amount=rw.get('amount', 0),
                    miner_type_id=rw.get('item_id') if rw['type'] == 'miner' else None,
                    transport_type_id=rw.get('item_id') if rw['type'] == 'transport' else None,
                    tool_type_id=rw.get('item_id') if rw['type'] == 'tool' else None,
                )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def level_update(request, pk):
    try:
        level = get_object_or_404(SeasonLevel, pk=pk)
        data = json.loads(request.body)
        with transaction.atomic():
            level.name = data['name']
            level.lock_duration_days = data.get('lock_duration_days', 7)
            level.save()
            
            # Update requirements
            level.requirements.all().delete()
            requirements = data.get('requirements', [])
            for r in requirements:
                SeasonLevelRequirement.objects.create(
                    level=level,
                    requirement_type=r['type'],
                    value=r['value']
                )
            # Update rewards
            level.rewards.all().delete()
            rewards = data.get('rewards', [])
            for rw in rewards:
                SeasonLevelReward.objects.create(
                    level=level,
                    reward_type=rw['type'],
                    amount=rw.get('amount', 0),
                    miner_type_id=rw.get('item_id') if rw['type'] == 'miner' else None,
                    transport_type_id=rw.get('item_id') if rw['type'] == 'transport' else None,
                    tool_type_id=rw.get('item_id') if rw['type'] == 'tool' else None,
                )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def level_delete(request, pk):
    try:
        level = get_object_or_404(SeasonLevel, pk=pk)
        level.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@login_required
def public_rankings_page(request):
    return render(request, "game/rankings.html")
