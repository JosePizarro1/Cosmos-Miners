import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import *
from .models_rankings import UserSeasonEntry

def _parse_bool(value):
    if value is None: return False
    return str(value).lower() in {"1", "true", "on", "yes"}

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
            gold_value = request.POST.get('gold_value', 0)
            image = request.FILES.get('image')
            Mineral.objects.create(name=name, image=image, gold_value=gold_value)
            messages.success(request, f"Mineral {name} creado con valor {gold_value} Gold.")
            
        elif action == 'add_planet':
            name = request.POST.get('name')
            time = request.POST.get('travel_time')
            success = request.POST.get('success_rate')
            puntos = request.POST.get('puntos', 0)
            is_free = _parse_bool(request.POST.get('is_free'))
            is_alliance = _parse_bool(request.POST.get('is_alliance'))
            price_gold = request.POST.get('price_gold', 0)
            price_mineral_id = request.POST.get('price_mineral')
            price_mineral_qty = request.POST.get('price_mineral_quantity', 0)
            required_miners = request.POST.get('required_miners', 0)
            required_tools = request.POST.get('required_tools', 0)
            required_transports = request.POST.get('required_transports', 0)
            image = request.FILES.get('image')

            Planet.objects.create(
                name=name,
                travel_time_base=time,
                success_rate_base=success,
                puntos=puntos,
                is_free=is_free,
                is_alliance=is_alliance,
                price_gold=price_gold,
                price_mineral_id=price_mineral_id if price_mineral_id else None,
                price_mineral_quantity=price_mineral_qty if price_mineral_qty else 0,
                required_miners=required_miners if required_miners else 0,
                required_tools=required_tools if required_tools else 0,
                required_transports=required_transports if required_transports else 0,
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
            planet.is_free = _parse_bool(request.POST.get('is_free'))
            planet.is_alliance = _parse_bool(request.POST.get('is_alliance'))
            planet.price_gold = request.POST.get('price_gold', 0)
            
            p_mineral_id = request.POST.get('price_mineral')
            planet.price_mineral_id = p_mineral_id if p_mineral_id else None
            planet.price_mineral_quantity = request.POST.get('price_mineral_quantity', 0) or 0
            
            planet.required_miners = request.POST.get('required_miners', 0) or 0
            planet.required_tools = request.POST.get('required_tools', 0) or 0
            planet.required_transports = request.POST.get('required_transports', 0) or 0
            
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
            mineral.gold_value = request.POST.get('gold_value', 0)
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
    # Filter planets: public planets + exclusive planets owned by user's alliance
    from django.db.models import Q
    from .models_alliances import AlliancePlanet
    
    if profile.alliance:
        owned_ids = AlliancePlanet.objects.filter(alliance=profile.alliance).values_list('planet_id', flat=True)
        planets = Planet.objects.prefetch_related('produced_minerals__mineral').filter(
            is_active=True
        ).filter(
            Q(is_alliance=False) | Q(id__in=owned_ids)
        )
    else:
        planets = Planet.objects.prefetch_related('produced_minerals__mineral').filter(
            is_active=True, is_alliance=False
        )
    
    # Check if alliance is already on a mission to an alliance planet
    # ONLY one alliance planet can be mined at a time per alliance
    alliance_busy = False
    if profile.alliance:
        # Check if ANY member of the same alliance is in an 'ongoing' trip to any 'is_alliance' planet
        from .models_planets import MiningTrip
        alliance_busy = MiningTrip.objects.filter(
            user__profile__alliance=profile.alliance,
            planet__is_alliance=True,
            status='ongoing'
        ).exists()

    # Get active seasons where the user is enrolled
    now_dt = timezone.now()
    user_seasons = list(UserSeasonEntry.objects.filter(
        user=request.user,
        season__start_date__lte=now_dt,
        season__end_date__gte=now_dt
    ).values_list('season_id', flat=True))

    # Determine lock status for each planet
    user_miner_total = UserMiner.objects.filter(owner=profile).count()
    user_tool_total = UserTool.objects.filter(owner=profile).count()
    user_transport_total = UserTransport.objects.filter(owner=profile).count()

    for p in planets:
        p.requirement_met = True
        if not p.is_free and not p.is_alliance:
            if p.required_miners > user_miner_total:   p.requirement_met = False
            if p.required_tools > user_tool_total:     p.requirement_met = False
            if p.required_transports > user_transport_total: p.requirement_met = False

    # Get active rankings info
    from .models_rankings import Season
    active_seasons = Season.objects.filter(start_date__lte=now_dt, end_date__gte=now_dt)

    # Calculate total victory bonus from active blessings
    blessing_bonus = 0.0
    from .models_blessings import UserBlessingClaim
    claims = UserBlessingClaim.objects.filter(user=request.user, static_blessing__isnull=False)
    for c in claims:
        blessing_bonus += float(c.static_blessing.bonus_percentage)

    return render(request, 'game/prepare_trip.html', {
        'miners': miners,
        'tools': tools,
        'transports': transports,
        'planets': planets,
        'user_seasons': user_seasons,
        'active_seasons': active_seasons, # Pass for ranking info
        'blessing_bonus': blessing_bonus,
        'alliance_busy': alliance_busy,
        'now': now_dt,
        'user_miner_total': user_miner_total,
        'user_tool_total': user_tool_total,
        'user_transport_total': user_transport_total,
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
        
        # Concurrency limit for Alliance Planets
        from .models_planets import MiningTrip
        if planet.is_alliance and profile.alliance:
            if MiningTrip.objects.filter(
                user__profile__alliance=profile.alliance,
                planet__is_alliance=True,
                status='ongoing'
            ).exists():
                messages.error(request, "Tu alianza ya tiene una expedición activa en un planeta especial. Deben esperar a que regrese para enviar otra.")
                return redirect('mining_dashboard')
        
        # Check compatibility (Free vs Paid) — Alliance planets are exempt
        if not planet.is_alliance:
            planet_free = planet.is_free
            if miner.miner_type.is_free != planet_free or \
               tool.tool_type.is_free != planet_free or \
               transport.transport_type.is_free != planet_free:
                messages.error(request, "Compatibilidad de misión fallida: Los mundos GRATIS solo se exploran con activos GRATIS. Activos premium requieren mundos premium.")
                return redirect('mining_dashboard')

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
        puntos_base = trip.planet.puntos
        multiplier = 1.0
        miner_type = trip.miner.miner_type
        
        if miner_type.points_multiplier > 1:
            # Check if multiplier applies (no season required OR user enrolled in ACTIVE required season)
            now = timezone.now()
            if not miner_type.season or UserSeasonEntry.objects.filter(
                user=request.user, 
                season=miner_type.season,
                season__start_date__lte=now,
                season__end_date__gte=now
            ).exists():
                multiplier = float(miner_type.points_multiplier)
        
        won_points = int(puntos_base * multiplier)
        
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
