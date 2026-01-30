from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from game.models import Profile
from decimal import Decimal
from uuid import uuid4

User = get_user_model()


class Command(BaseCommand):
    help = 'Create Profile objects for users that are missing them'

    def handle(self, *args, **options):
        created = 0
        for u in User.objects.all():
            p, created_flag = Profile.objects.get_or_create(
                user=u,
                defaults={
                    'wallet_metamask_bsc': f"init_{u.id}_{uuid4().hex[:8]}",
                    'cosmos_gold': Decimal('0.00')
                }
            )
            if created_flag:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Profiles created: {created}'))
