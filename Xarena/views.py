from django.shortcuts import render
from tourney.models import Tournament
from accounts.models import Game


def index(request):
    tourney = Tournament.objects.filter(tourney_end=True).last()
    if tourney:
        context = {
            'game': Game.objects.last(),
            'tourney': tourney,
            "first": tourney.subscription_set.get(elimination_number=1).membership().user_name,
            "second": tourney.subscription_set.get(elimination_number=2).membership().user_name,
            "third": tourney.subscription_set.get(elimination_number=3).membership().user_name
        }
    else:
        context = {}
    u_tourney = [i for i in Tournament.objects.all() if not (i.is_live() or i.tourney_end)]
    context["u_tourney"] = u_tourney[0] if len(u_tourney) != 0 else None
    context["game"] = Game.objects.last() or None
    if len([i for i in Tournament.objects.all() if i.is_live()])!=0:
        context["l_tourney"] = [i for i in Tournament.objects.all() if i.is_live ][0] or None
    return render(request, "index.html", context)


def t_and_c(request):
    return render(request, "t&c.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html")

