from django.shortcuts import render
from tourney.models import Tournament


def index(request):
    tourney = Tournament.objects.filter(tourney_end=True).last()
    if tourney:
        context = {
            'tourney': tourney,
            "first": tourney.subscription_set.get(elimination_number=1).membership().user_name,
            "second": tourney.subscription_set.get(elimination_number=2).membership().user_name,
            "third": tourney.subscription_set.get(elimination_number=3).membership().user_name
        }
    else:
        context = {}
    return render(request, "index.html", context)


def t_and_c(request):
    return render(request, "t&c.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html")

