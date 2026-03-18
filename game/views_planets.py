import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import *
from .models_rankings import UserSeasonEntry

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def planets_admin(request):
    """Dashboard to manage minerals and planets."""
    minerals = Mineral.objects.all()
    planets = Planet.objects.all()
    ongoing_count = MiningTrip.objects.filter(status='ongoing').count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_mineral':
            name = request.POST.get('name')
            image = request.FILES.get('image')
            Mineral.objects.create(name=name, image=image)
            messages.success(request, f"Mineral {name} creado.")
            
        elif action == 'add_planet':
            name = request.POST.get('name')
            time = request.POST.get('travel_time')
            success = request.POST.get('success_rate')
            puntos = request.POST.get('puntos', 0)
            image = request.FILES.get('image')
            Planet.objects.create(
                name=name,
                travel_time_base=time,
                success_rate_base=success,
                puntos=puntos,
                image=image
            )
            messages.success(request, f"Planeta {name} creado.")
            
        elif action == 'add_planet_mineral':
            planet_id = request.POST.get('planet_id')
            mineral_id = request.POST.get('mineral_id')
            min_amt = request.POST.get('min_amount')
            max_amt = request.POST.get('max_amount')
            
            planet = Planet.objects.get(id=planet_id)
            mineral = Mineral.objects.get(id=mineral_id)
            
            PlanetMineral.objects.create(
                planet=planet,
                mineral=mineral,
                min_amount=min_amt,
                max_amount=max_amt
            )
            messages.success(request, f"Mineral {mineral.name} añadido a {planet.name}.")

        elif action == 'edit_planet':
            planet_id = request.POST.get('planet_id')
            planet = get_object_or_404(Planet, id=planet_id)
            planet.name = request.POST.get('name')
            planet.travel_time_base = request.POST.get('travel_time')
            planet.success_rate_base = request.POST.get('success_rate')
            planet.puntos = request.POST.get('puntos', 0)
            if request.FILES.get('image'):
                planet.image = request.FILES.get('image')
            planet.save()
            messages.success(request, f"Planeta {planet.name} actualizado.")

        elif action == 'delete_planet':
            planet_id = request.POST.get('planet_id')
            planet = get_object_or_404(Planet, id=planet_id)
            name = planet.name
            planet.delete()
            messages.success(request, f"Planeta {name} eliminado.")

        elif action == 'edit_mineral':
            mineral_id = request.POST.get('mineral_id')
            mineral = get_object_or_404(Mineral, id=mineral_id)
            mineral.name = request.POST.get('name')
            if request.FILES.get('image'):
                mineral.image = request.FILES.get('image')
            mineral.save()
            messages.success(request, f"Mineral {mineral.name} actualizado.")

        elif action == 'delete_mineral':
            mineral_id = request.POST.get('mineral_id')
            mineral = get_object_or_404(Mineral, id=mineral_id)
            name = mineral.name
            mineral.delete()
            messages.success(request, f"Mineral {name} eliminado.")

        elif action == 'delete_planet_mineral':
            pm_id = request.POST.get('pm_id')
            pm = get_object_or_404(PlanetMineral, id=pm_id)
            pm.delete()
            messages.success(request, "Vínculo de mineral eliminado.")

        elif action == 'force_finish':
            trips = MiningTrip.objects.filter(status='ongoing')
            count = trips.count()
            if count > 0:
                past_time = timezone.now() - timedelta(minutes=1)
                trips.update(end_time=past_time)
                messages.success(request, f"⚡ {count} viaje(s) adelantado(s). Ya se pueden reclamar.")
            else:
                messages.warning(request, "No hay viajes activos para adelantar.")

        return redirect('planets_admin')

    return render(request, 'game/planets_admin.html', {
        'minerals': minerals,
        'planets': planets,
        'ongoing_count': ongoing_count,
    })

@login_required
def mining_dashboard(request):
    """View for the user to select assets and start a trip."""
    profile = request.user.profile
    # Only idle assets
    miners = UserMiner.objects.filter(owner=profile, status=MinerStatus.IDLE)
    tools = UserTool.objects.filter(owner=profile, status=ToolStatus.IDLE)
    transports = UserTransport.objects.filter(owner=profile, status=TransportStatus.IDLE)
    planets = Planet.objects.filter(is_active=True)
    
    active_trips = MiningTrip.objects.filter(user=request.user).exclude(status='collected')
    
    # User's current minerals
    user_minerals = UserMineral.objects.filter(user=request.user)

    return render(request, 'game/mining_dashboard.html', {
        'miners': miners,
        'tools': tools,
        'transports': transports,
        'planets': planets,
        'active_trips': active_trips,
        'user_minerals': user_minerals,
    })

@login_required
def prepare_trip(request):
    """Full-page wizard to select assets and planet for a new trip."""
    profile = request.user.profile
    miners = UserMiner.objects.filter(owner=profile, status=MinerStatus.IDLE)
    tools = UserTool.objects.filter(owner=profile, status=ToolStatus.IDLE)
    transports = UserTransport.objects.filter(owner=profile, status=TransportStatus.IDLE)
    planets = Planet.objects.prefetch_related('produced_minerals__mineral').filter(is_active=True)

    return render(request, 'game/prepare_trip.html', {
        'miners': miners,
        'tools': tools,
        'transports': transports,
        'planets': planets,
    })

@login_required
def start_mining_trip(request):
    if request.method != 'POST':
        return redirect('mining_dashboard')
        
    miner_id = request.POST.get('miner_id')
    tool_id = request.POST.get('tool_id')
    transport_id = request.POST.get('transport_id')
    planet_id = request.POST.get('planet_id')
    
    try:
        profile = request.user.profile
        miner = UserMiner.objects.get(id=miner_id, owner=profile, status=MinerStatus.IDLE)
        tool = UserTool.objects.get(id=tool_id, owner=profile, status=ToolStatus.IDLE)
        transport = UserTransport.objects.get(id=transport_id, owner=profile, status=TransportStatus.IDLE)
        planet = Planet.objects.get(id=planet_id, is_active=True)
        
        # Calculations
        # 1. Travel Time (modified by transport speed)
        # speed 100% = 1.0 multiplier. Time = base / (speed/100)
        speed_mult = transport.transport_type.speed / 100.0
        if speed_mult <= 0: speed_mult = 1.0
        final_hours = planet.travel_time_base / speed_mult
        
        # 2. Success Rate (base planet only)
        final_success = planet.success_rate_base
        if final_success > 100: final_success = 100
        
        # 3. Attempts (from miner)
        final_attempts = miner.miner_type.attempts
        
        # 4. Production Multiplier (from tool bonus_pct: 100%=x1, 200%=x2)
        prod_mult = float(tool.tool_type.bonus_pct) / 100.0
        
        # Create Trip
        end_time = timezone.now() + timedelta(hours=final_hours)
        
        trip = MiningTrip.objects.create(
            user=request.user,
            planet=planet,
            miner=miner,
            tool=tool,
            transport=transport,
            end_time=end_time,
            attempts=final_attempts,
            success_rate=int(final_success),
            production_multiplier=prod_mult
        )
        
        # Update Asset Status
        miner.status = MinerStatus.TRAVELING
        miner.save()
        tool.status = ToolStatus.TRAVELING
        tool.save()
        transport.status = TransportStatus.TRAVELING
        transport.save()
        
        messages.success(request, f"¡Viaje iniciado con destino a {planet.name}! Llegada estimada: {end_time.strftime('%H:%M:%S')}")
        
    except (UserMiner.DoesNotExist, UserTool.DoesNotExist, UserTransport.DoesNotExist, Planet.DoesNotExist) as e:
        messages.error(request, f"Error al iniciar viaje: Elementos no válidos o en uso. {str(e)}")
        
    return redirect('mining_dashboard')

@login_required
def collect_mining_trip(request, trip_id):
    trip = get_object_or_404(MiningTrip, id=trip_id, user=request.user, status='ongoing')
    
    if timezone.now() < trip.end_time:
        messages.warning(request, "El viaje aún no ha terminado.")
        return redirect('mining_dashboard')
        
    # Calculate Results - DETAILED per attempt
    produced_minerals = PlanetMineral.objects.filter(planet=trip.planet)
    totals = {}
    attempts_detail = []
    
    for i in range(trip.attempts):
        roll = random.randint(1, 100)
        success = roll <= trip.success_rate
        
        attempt_data = {
            'number': i + 1,
            'roll': roll,
            'needed': trip.success_rate,
            'success': success,
            'minerals': []
        }
        
        if success:
            for pm in produced_minerals:
                min_final = int(float(pm.min_amount) * float(trip.production_multiplier))
                max_final = int(float(pm.max_amount) * float(trip.production_multiplier))
                amount_mined = random.randint(min_final, max_final)
                
                attempt_data['minerals'].append({
                    'name': pm.mineral.name,
                    'amount': amount_mined,
                })
                totals[pm.mineral.name] = totals.get(pm.mineral.name, 0) + amount_mined
        
        attempts_detail.append(attempt_data)
    
    # Save Results
    trip.results_json = totals
    trip.status = 'collected'
    trip.save()
    
    # Update User Inventory
    for mineral_name, amount in totals.items():
        mineral = Mineral.objects.get(name=mineral_name)
        um, created = UserMineral.objects.get_or_create(user=request.user, mineral=mineral)
        um.amount += amount
        um.save()
        
    # Release Assets
    trip.miner.status = MinerStatus.IDLE
    trip.miner.save()
    trip.tool.status = ToolStatus.IDLE
    trip.tool.save()
    trip.transport.status = TransportStatus.IDLE
    trip.transport.save()

    successful_attempts = sum(1 for a in attempts_detail if a['success'])
    
    # Give points if at least 1 successful attempt
    won_points = 0
    if successful_attempts > 0:
        won_points = trip.planet.puntos
        if won_points > 0:
            profile = request.user.profile
            profile.points += won_points
            profile.save()
            
            # Give points to active ranking entries
            active_entries = UserSeasonEntry.objects.filter(
                user=request.user, 
                season__start_date__lte=timezone.now(),
                season__end_date__gte=timezone.now()
            )
            for entry in active_entries:
                entry.points += won_points
                entry.save()
    
    return render(request, 'game/mining_results.html', {
        'trip': trip,
        'attempts_detail': attempts_detail,
        'totals': totals,
        'total_attempts': trip.attempts,
        'successful_attempts': successful_attempts,
        'won_points': won_points,
    })
