from django.views.generic import ListView, DetailView, CreateView
from accounts.models import Game, Membership
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Tournament, Subscription
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
import json


class Store(ListView):
    template_name = 'tourney/store_list.html'
    model = Game


class Detail(DetailView):
    template_name = 'tourney/game_detail.html'
    model = Game


class Subscribe(LoginRequiredMixin,CreateView):
    model = Membership
    fields = [ "user_name","user_id"]
    template_name = "tourney/subscribe.html"

    def form_valid(self, form):
        form.instance.player = self.request.user
        form.instance.game = Game.objects.get(pk=self.kwargs['pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("store")


class Tourney(LoginRequiredMixin, ListView):
    model = Tournament
    template_name = "tourney/tournaments.html"



@login_required
def tourney_detail(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    if request.user not in tourney.game.users.all():
        messages.warning(request,"To participate in tournament you need to subscribe to the game first")
        return redirect("detail", pk=tourney.game.pk)

    if request.method == "POST":
        if request.user.profile.account_balance < tourney.price:
            messages.error(request,"sorry your wallet balance is less than tournament price. please add some credits to your wallet")
            return redirect("transfer")
        if request.user in tourney.players.all():
            messages.warning("you are already in tournament")
            return redirect("tournament_detail", pk = tourney.pk)
        user_acc = request.user.profile
        user_acc.account_balance -= tourney.price
        user_acc.save()
        tourney.players.add(request.user)
        return redirect("tournament_detail", pk = tourney.pk)

    if request.user in tourney.players.all() :
        user_exist = tourney.players.get(id=request.user.id).username
    else:
        user_exist = ""
    special = json.loads(tourney.special)
    context = {
        "special":special,
        "user_exist": user_exist,
        "object": tourney
    }

    return render(request, "tourney/tournament_detail.html", context)


@login_required
def live_tourney(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    context = {
        "object" : tourney
    }
    return render(request, "tourney/live_tourney.html", context)