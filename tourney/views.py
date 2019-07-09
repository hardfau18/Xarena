from django.views.generic import ListView, DetailView, CreateView
from accounts.models import Game, Membership
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Tournament, Subscription
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from paytm import checksum
from django.contrib import messages

merchant_key = '5N1ZW7zBgXCoOiRZ'


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
        if request.user not in tourney.players.all():
            tourney.players.add(request.user)
        subscription = get_object_or_404(Subscription, tourney=tourney, player=request.user)
        subscription.membership = request.user.membership_set.get(game=tourney.game)
        subscription.save()
        if subscription.player_joined:
            return redirect("tournaments")

        oid = subscription.pk
        price = tourney.price
        params = {
            "MID": "eJvkxV73534228896310",
            "ORDER_ID": str(oid),
            "CUST_ID": request.user.email,
            "TXN_AMOUNT": str(price),
            "CHANNEL_ID": "WEB",
            "INDUSTRY_TYPE_ID": "Retail",
            "WEBSITE": "WEBSTAGING",
            'CALLBACK_URL': 'http://13.127.178.253/tournaments/handle-request'
        }

        params["CHECKSUMHASH"] = checksum.generate_checksum(params, merchant_key)
        return render(request, "tourney/paytm.html", {"params":params})

    if request.user in tourney.players.all() and Subscription.objects.get(tourney=tourney, player=request.user).player_joined :
        user_exist = tourney.players.get(id=request.user.id).username
    else:
        user_exist = ""
        if request.user in tourney.players.all():
            tourney.players.remove(request.user)

    context = {
        "user_exist": user_exist,
        "object": tourney
    }

    return render(request, "tourney/tournament_detail.html", context)


@csrf_exempt
def handle_request(request):
    if request.method != "POST":
        return HttpResponseBadRequest(content="<h1>Bad request 400</h1> <br/>invalid request")
    form = request.POST
    response = {}

    for i in form.keys():
        response[i] = form[i]
    code = checksum.verify_checksum(response, merchant_key, form['CHECKSUMHASH'])

    s = Subscription.objects.get(pk=form["ORDERID"])
    tourney = s.tourney

    if not code:
        return HttpResponseBadRequest(content="Transaction failed due to Hash missmatch")
    elif form['RESPCODE'] == '01':
        s.player_joined = True
        s.save()
    else:
        if request.user in tourney.players.all():
            tourney.players.remove(s.player)
        print('transaction ' + response['RESPMSG'])
    response["tourney_pk"] = tourney.pk
    return render(request, "tourney/payment_status.html", response)

