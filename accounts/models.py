from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.urls import reverse
from django.contrib.postgres.fields import ArrayField


User._meta.get_field('email')._unique = True


class Game(models.Model):
    users = models.ManyToManyField(User, through="Membership")
    name = models.CharField(max_length=20)
    image = models.ImageField(upload_to="images/game_profile", default="images/game_profile/default.png")
    desc = models.TextField()
    special = ArrayField(models.CharField(max_length=20), null=True, blank=True)

    def __str__(self):
        return self.name

class PaymentWindow(models.Model):
    name=models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/profile_pics", default="images/profile_pics/default.png")
    email_confirmed = models.BooleanField(default=False)
    wallet_balance = models.PositiveIntegerField(default=0)
    payment_options = models.ManyToManyField(PaymentWindow, through="PaymentNumber")

    def __str__(self):
        return f"{self.user.username} profile"

    def save(self, force_insert=False, force_update=False, using=None):
        super().save()
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


class PaymentNumber(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    payment_window = models.ForeignKey(PaymentWindow, on_delete=models.CASCADE)
    num = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.user.username} {self.payment_window}"

class Membership(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=50 )
    user_id = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user_name', 'user_id')

    def __str__(self):
        return self.user_name

    def get_absolute_url(self):
        return reverse('profile')


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    date_of_payment = models.DateTimeField(auto_now_add=True)
    transaction_success = models.BooleanField(default=False)



class ReqMoneyBack(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_window = models.ForeignKey(PaymentWindow, on_delete=models.CASCADE)
    pay_to = models.PositiveIntegerField()
    amount = models.PositiveIntegerField(default=0)
    trans_status = models.BooleanField(default=False)
    request_date = models.TimeField(auto_now_add=True)
    finish_date = models.TimeField(auto_now=True)

    def __str__(self):
        return self.user.username+" "+str(self.amount)
