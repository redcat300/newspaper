from django.contrib.auth.models import User
from news.models import Profile

def create_profiles():
    users_without_profiles = User.objects.filter(profile__isnull=True)
    for user in users_without_profiles:
        Profile.objects.create(user=user)
        print(f"Profile created for user: {user.username}")

if __name__ == "__main__":
    create_profiles()