from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from .models import (
    Chest, ChestCategory, ChestReward, 
    MinerType, TransportType, ToolType
)
import json
from decimal import Decimal

@login_required
@user_passes_test(lambda u: u.is_staff)
def chests_admin_view(request):
    return render(request, "game/chests_admin.html")

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def chests_list(request):
    chests = Chest.objects.select_related('category').all().order_by('-created_at')
    items = []
    for c in chests:
        rewards = []
        for r in c.rewards.all():
            reward_data = {
                "id": r.id,
                "display_probability": str(r.display_probability),
                "code_probability": str(r.code_probability),
            }
            if r.miner_reward:
                reward_data["type"] = "miner"
                reward_data["name"] = r.miner_reward.name
                reward_data["item_id"] = r.miner_reward.id
            elif r.transport_reward:
                reward_data["type"] = "transport"
                reward_data["name"] = r.transport_reward.name
                reward_data["item_id"] = r.transport_reward.id
            elif r.tool_reward:
                reward_data["type"] = "tool"
                reward_data["name"] = r.tool_reward.name
                reward_data["item_id"] = r.tool_reward.id
            rewards.append(reward_data)
            
        items.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "price": str(c.price),
            "is_in_store": c.is_in_store,
            "category_name": c.category.name if c.category else "Sin categoría",
            "category_id": c.category.id if c.category else None,
            "image_url": c.image.url if c.image else "",
            "rewards_per_open": c.rewards_per_open,
            "rewards": rewards
        })
    return JsonResponse({"success": True, "items": items})

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def chest_create(request):
    try:
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category_id = request.POST.get("category_id")
        is_in_store = request.POST.get("is_in_store") in ["true", "on"]
        rewards_per_open = request.POST.get("rewards_per_open", 1)
        image = request.FILES.get("image")
        
        # Rewards is a JSON string of objects
        rewards_raw = request.POST.get("rewards", "[]")
        rewards_data = json.loads(rewards_raw)

        with transaction.atomic():
            category = None
            if category_id:
                category = ChestCategory.objects.get(id=category_id)
                
            chest = Chest.objects.create(
                name=name,
                description=description,
                price=Decimal(price),
                category=category,
                is_in_store=is_in_store,
                rewards_per_open=int(rewards_per_open),
                image=image
            )
            
            for r in rewards_data:
                reward_type = r.get("type")
                item_id = r.get("item_id")
                disp_prob = Decimal(str(r.get("display_probability", 0)))
                code_prob = Decimal(str(r.get("code_probability", 0)))
                
                reward_params = {
                    "chest": chest,
                    "display_probability": disp_prob,
                    "code_probability": code_prob
                }
                
                if reward_type == "miner":
                    reward_params["miner_reward"] = MinerType.objects.get(id=item_id)
                elif reward_type == "transport":
                    reward_params["transport_reward"] = TransportType.objects.get(id=item_id)
                elif reward_type == "tool":
                    reward_params["tool_reward"] = ToolType.objects.get(id=item_id)
                
                ChestReward.objects.create(**reward_params)
                
        return JsonResponse({"success": True})
    except Exception as e:
        print("CHEST CREATE ERROR:", e)
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def chest_delete(request, pk):
    try:
        Chest.objects.get(pk=pk).delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_staff)
def chest_dependencies(request):
    # Fetch categories and all item types for the creation form
    categories = list(ChestCategory.objects.values("id", "name"))
    miners = list(MinerType.objects.filter(is_active=True).values("id", "name"))
    transports = list(TransportType.objects.filter(is_active=True).values("id", "name"))
    tools = list(ToolType.objects.filter(is_active=True).values("id", "name"))
    
    return JsonResponse({
        "success": True,
        "categories": categories,
        "items": {
            "miner": miners,
            "transport": transports,
            "tool": tools
        }
    })

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def chest_update(request, pk):
    try:
        chest = Chest.objects.get(pk=pk)
        chest.name = request.POST.get("name")
        chest.description = request.POST.get("description")
        chest.price = Decimal(request.POST.get("price"))
        chest.rewards_per_open = int(request.POST.get("rewards_per_open", 1))
        
        category_id = request.POST.get("category_id")
        if category_id:
            chest.category = ChestCategory.objects.get(id=category_id)
            
        chest.is_in_store = request.POST.get("is_in_store") in ["true", "on"]
        
        if request.FILES.get("image"):
            chest.image = request.FILES.get("image")
            
        rewards_raw = request.POST.get("rewards", "[]")
        rewards_data = json.loads(rewards_raw)
        
        with transaction.atomic():
            chest.save()
            chest.rewards.all().delete()
            for r in rewards_data:
                reward_type = r.get("type")
                item_id = r.get("item_id")
                disp_prob = Decimal(str(r.get("display_probability", 0)))
                code_prob = Decimal(str(r.get("code_probability", 0)))
                
                reward_params = {
                    "chest": chest,
                    "display_probability": disp_prob,
                    "code_probability": code_prob
                }
                
                if reward_type == "miner":
                    reward_params["miner_reward"] = MinerType.objects.get(id=item_id)
                elif reward_type == "transport":
                    reward_params["transport_reward"] = TransportType.objects.get(id=item_id)
                elif reward_type == "tool":
                    reward_params["tool_reward"] = ToolType.objects.get(id=item_id)
                
                ChestReward.objects.create(**reward_params)
                
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def chest_toggle(request, pk):
    try:
        chest = Chest.objects.get(pk=pk)
        chest.is_in_store = not chest.is_in_store
        chest.save()
        return JsonResponse({"success": True, "is_in_store": chest.is_in_store})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def category_list(request):
    try:
        categories = list(ChestCategory.objects.all().values("id", "name"))
        return JsonResponse({"success": True, "items": categories})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def category_create(request):
    try:
        data = json.loads(request.body)
        name = data.get("name")
        if not name:
            return JsonResponse({"error": "Nombre requerido"}, status=400)
        category = ChestCategory.objects.create(name=name)
        return JsonResponse({"success": True, "id": category.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def category_update(request, pk):
    try:
        data = json.loads(request.body)
        name = data.get("name")
        category = ChestCategory.objects.get(pk=pk)
        category.name = name
        category.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_protect
@login_required
@user_passes_test(lambda u: u.is_staff)
def category_delete(request, pk):
    try:
        category = ChestCategory.objects.get(pk=pk)
        if category.chest_set.exists():
            return JsonResponse({"error": "No se puede eliminar una categoría con cofres asociados"}, status=400)
        category.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
