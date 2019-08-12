from django.contrib import admin
from .models import Tournament, Subscription, TourneyObject


admin.site.register(Tournament)
admin.site.register(Subscription)
admin.site.register(TourneyObject)