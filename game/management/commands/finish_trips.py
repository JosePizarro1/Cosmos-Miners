from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from game.models_planets import MiningTrip


class Command(BaseCommand):
    help = 'Adelanta todos los viajes activos para que terminen ya (para testing)'

    def handle(self, *args, **options):
        trips = MiningTrip.objects.filter(status='ongoing')
        count = trips.count()

        if count == 0:
            self.stdout.write(self.style.WARNING('No hay viajes activos para adelantar.'))
            return

        # Poner el end_time 1 minuto en el pasado
        past_time = timezone.now() - timedelta(minutes=1)
        trips.update(end_time=past_time)

        self.stdout.write(self.style.SUCCESS(
            f'✅ {count} viaje(s) adelantado(s). Ya puedes reclamar los recursos.'
        ))
