from django.views.generic import ListView, DetailView, CreateView
from accounts.models import Game, Membership
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Tournament, Subscription
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required


def distribute_prize(t):
    players = t.subscription_set
    first = players.get(elimination_number=1)
    first.player.profile.account_balance += t.first_prize
    first.player.profile.save()

    second = players.get(elimination_number=2)
    second.player.profile.account_balance += t.second_prize
    second.player.profile.save()

    third = players.get(elimination_number=3)
    third.player.profile.account_balance += t.third_prize
    third.player.profile.save()

    if t.bonus :
        for sub in players.all():
            sub.player.profile.account_balance += sub.bonus_count() * t.bonus
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
        user_acc.account_balance -= tourney.entry_fee
        user_acc.save()
        tourney.players.add(request.user)
        return redirect("tournament_detail", pk = tourney.pk)

    if request.user in tourney.players.all() :
        user_exist = tourney.players.get(id=request.user.id).username
    else:
        user_exist = ""
    context = {
        "user_exist": user_exist,
        "object": tourney
    }

    return render(request, "tourney/tournament_detail.html", context)


@login_required
def live_tourney(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    if tourney.tourney_end:
        messages.warning(request, "Tournament has ended")
        return redirect("tournament_result", pk=pk)

    context = {
        "live_players": [x for x in tourney.subscription_set.all() if x.active()],
        "subs": tourney.subscription_set.all(),
        "object": tourney
    }
    return render(request, "tourney/live_tourney.html", context)


@staff_member_required(login_url="login")
def tourney_manage(request, pk):
    tourney = get_object_or_404(Tournament,pk=pk)
    return redirect("tourney_manage_"+tourney.tourney_type.mode, pk=pk)


@staff_member_required
def tourney_manage_Survival(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    subs = tourney.subscription_set.all()
    if tourney.tourney_type.mode!="Survival":
        messages.error(request, "Stop cheating, you are on wrong manage mode. You will be reported.")
        return redirect("live_tourney", pk=pk)
    if tourney.tourney_end:
        messages.warning(request, "Tournament has ended")
        return redirect("tournament_result", pk=pk)
    if request.method == "POST":
        print(request.POST.get("eliminated"))
        eliminator = get_object_or_404(Membership, user_name=request.POST.get("eliminator"))
        eliminated = get_object_or_404(Membership, user_name=request.POST.get("eliminated"))
        print("stage passed")
        sub = subs.get(player=eliminated.player)
        sub.eliminated_by = subs.get(player=eliminator.player)
        sub.elimination_number = tourney.elimination_count()
        sub.save()
        if tourney.elimination_count() == 1:
            s = subs.get(elimination_number=None)
            s.elimination_number = 1
            s.save()
            tourney.tourney_end = True
            distribute_prize(tourney)
            tourney.save()
        return redirect("tourney_manage", pk=pk)

    context = {
        "subs": tourney.subscription_set.all(),
        "object":tourney
    }
    return render(request, "tourney/tourney_manage_Survival.html", context)


@login_required
def tourney_results(request, pk):
    tourney = get_object_or_404(Tournament, pk=pk)
    context = {
        "object":tourney,
        "first":tourney.subscription_set.get(elimination_number=1).membership().user_name,
        "second":tourney.subscription_set.get(elimination_number=2).membership().user_name,
        "third":tourney.subscription_set.get(elimination_number=3).membership().user_name,
        "subs": tourney.subscription_set.all().order_by("elimination_number")
    }
    return render(request, "tourney/tourney_results.html", context)