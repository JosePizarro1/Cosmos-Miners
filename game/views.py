from django.shortcuts import render
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from .models import Profile
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


def login_page(request):
    return render(request, "game/login.html")

def register_view(request):
    return render(request, "game/register.html")

@login_required
def home_view(request):
    return render(request, "game/home.html")

@require_POST
@csrf_protect
def login_view(request):
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({"error": "Credenciales inválidas"}, status=401)

        login(request, user)
        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    except Exception as e:
        print("LOGIN ERROR:", e)
        return JsonResponse({"error": "Error interno"}, status=500)
    
@require_POST
@csrf_protect
def register(request):
    try:
        data = json.loads(request.body)

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password")
        password2 = data.get("password2")
        wallet = data.get("wallet", "").strip()

        if not all([username, email, password, password2, wallet]):
            return JsonResponse({"error": "Campos incompletos"}, status=400)

        if password != password2:
            return JsonResponse({"error": "Las contraseñas no coinciden"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Usuario ya existe"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email ya registrado"}, status=400)

        if Profile.objects.filter(wallet_metamask_bsc=wallet).exists():
            return JsonResponse({"error": "Wallet ya registrada"}, status=400)

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            Profile.objects.create(
                user=user,
                wallet_metamask_bsc=wallet
            )

        return JsonResponse({"success": True}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    except Exception as e:
        print("REGISTER ERROR:", e)  # 🔴 SOLO PARA DEBUG
        return JsonResponse({"error": "Error interno"}, status=500)