from django.db import models
from django.contrib.auth.models import User
from accounts.models import Game, Membership


class Tournament(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    players = models.ManyToManyField(User, blank=True, through="Subscription")
    max_players = models.IntegerField(default=100)
    tourney_type = models.CharField(max_length=20)
    price = models.IntegerField()
    time = models.DateTimeField()


    def __str__(self):
        return self.game.name

    def players_joined(self):
        return len(self.players.all())


class Subscription(models.Model):
    tourney = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, null=True)
    subscription_id = models.AutoField(primary_key=True,)
    player_joined = models.BooleanField(default=False)

    def __str__(self):
        return self.player.username + "_" + self.tourney.game.name
