from django.views.generic import ListView, DetailView, CreateView
from accounts.models import Game, Membership
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Tournament, Subscription
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
import json
from django.contrib.admin.views.decorators import staff_member_required


def distribute_prize(t):
    players = t.subscription_set
    first = players.get(knock_out_number=1)
    first.player.profile.account_balance += t.first_prize
    first.player.profile.save()

    second = players.get(knock_out_number=2)
    second.player.profile.account_balance += t.second_prize
    second.player.profile.save()

    third = players.get(knock_out_number=3)
    third.player.profile.account_balance += t.third_prize
    third.player.profile.save()

    if t.special :
        for sub in players.all():
            sub.player.profile.account_balance += len(sub.subscription_set.all()) * json.loads(t.special)["prize_per_kill"]
            sub.player.profile.save()


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
    special = json.loads(tourney.special)

    context = {
        "live_players":[x for x in tourney.subscription_set.all() if x.is_alive],
        "subs": tourney.subscription_set.all(),
        "special":special,
        "object" : tourney
    }
    return render(request, "tourney/live_tourney.html", context)


@staff_member_required
def tourney_manage(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    if tourney.tourney_end:
        messages.warning(request, "Tournament has ended")
        return redirect("store")
    players = len(tourney.players.all())
    if request.method=="POST":
        killer = get_object_or_404(Membership, user_name=request.POST.get("killer"))
        kill = get_object_or_404(Membership, user_name=request.POST.get("kill"))
        subs = get_object_or_404(Subscription, membership=kill)
        subs.is_alive = False
        subs.killed_by = get_object_or_404(Subscription, membership=killer)
        subs.knock_out_number = players - tourney.knocked
        subs.save()
        tourney.knocked += 1
        tourney.save()
        if tourney.knocked == players - 1:
            print("success")
            s=Subscription.objects.get(is_alive=True)
            s.knock_out_number = 1
            s.save()
            tourney.tourney_end = True
            distribute_prize(tourney)
            tourney.save()
        return redirect("tourney_manage", pk=pk)

    context = {
        "subs": tourney.subscription_set.all().order_by('membership'),
        "object":tourney
    }
    return render(request, "tourney/tourney_manage.html", context)


@login_required
def tourney_results(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    context = {
        "object":tourney,
        "first":tourney.subscription_set.get(knock_out_number=1).membership.user_name,
        "second":tourney.subscription_set.get(knock_out_number=2).membership.user_name,
        "third":tourney.subscription_set.get(knock_out_number=3).membership.user_name,
        "subs": tourney.subscription_set.all().order_by('membership')
    }
    return render(request, "tourney/tourney_results.html", context)