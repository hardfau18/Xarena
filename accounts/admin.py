from django.contrib import admin
from .models import Profile, Game,ReqMoneyBack, Membership


admin.site.register(Profile)
admin.site.register(Game)
admin.site.register(Membership)
admin.site.register(ReqMoneyBack)