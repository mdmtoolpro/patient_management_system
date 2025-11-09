from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import StaffProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create missing StaffProfile for existing users'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        
        self.stdout.write(f'Found {users_without_profiles.count()} users without profiles')
        
        for user in users_without_profiles:
            StaffProfile.objects.create(user=user)
            self.stdout.write(
                self.style.SUCCESS(f'Created profile for {user.email}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('All missing profiles have been created!')
        )