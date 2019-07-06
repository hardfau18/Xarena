from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.urls import reverse


User._meta.get_field('email')._unique = True


class Game(models.Model):
    users = models.ManyToManyField(User, through="Membership")
    name = models.CharField(max_length=20)
    image = models.ImageField(upload_to="images/game_profile", default="images/game_profile/default.png")
    desc = models.TextField()

    def __str__(self):
        return self.name





class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/profile_pics", default="images/profile_pics/default.png")
    email_confirmed = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.user.username} profile"

    def save(self, force_insert=False, force_update=False, using=None):
        super().save()
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)



class Membership(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=50, unique=True)
    user_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.user_name


    def get_absolute_url(self):
        return reverse('profile')
