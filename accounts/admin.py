from django.contrib import admin
from .models import Profile, Game,ReqMoneyBack, Membership,PaymentWindow, PaymentNumber


admin.site.register(Profile)
admin.site.register(Game)
admin.site.register(Membership)
admin.site.register(ReqMoneyBack)
admin.site.register(PaymentWindow)
admin.site.register(PaymentNumber)