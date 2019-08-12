from django.shortcuts import render


def index(request):
    context = {

    }
    return render(request, "index.html", context)

def t_and_c(request):
    return render(request, "t&c.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html")

