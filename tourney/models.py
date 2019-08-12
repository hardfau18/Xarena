from django.db import models
from django.contrib.auth.models import User
from accounts.models import Game, Membership
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class TourneyObject(models.Model):
    mode = models.CharField(max_length=20)
    bonus = models.CharField(max_length=30)

    def __str__(self):
        return self.mode


class Tournament(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    players = models.ManyToManyField(User, blank=True, through="Subscription")
    max_players = models.IntegerField(default=100)
    tourney_type = models.ForeignKey(TourneyObject, on_delete=models.CASCADE)
    entry_fee = models.IntegerField()
    time = models.DateTimeField()
    tourney_id = models.CharField(max_length=50)
    tourney_pass = models.CharField(max_length=15)
    first_prize = models.IntegerField()
    second_prize = models.IntegerField()
    third_prize = models.IntegerField()
    bonus_prize = models.IntegerField()
    tourney_end = models.BooleanField(default=False)

    def elimination_count(self):
        return len([i for i in self.subscription_set.all() if i.active()])

    def is_live(self):
        return True if self.time <= timezone.now() and not self.tourney_end else False

    def __str__(self):
        return self.game.name+" "+str(self.time)

    def players_joined(self):
        return len(self.players.all())


class Subscription(models.Model):
    tourney = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_id = models.AutoField(primary_key=True,)
    bonus_count = models.PositiveIntegerField(default=0)
    elimination_number = models.PositiveIntegerField(null=True, blank=True)
    eliminated_by = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.player.username + "_" + self.tourney.game.name

    def active(self):
        return True if self.elimination_number is None else False

    def membership(self):
        return self.player.membership_set.get(game=self.tourney.game)
