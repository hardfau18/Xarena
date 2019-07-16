from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, AmountTransfer
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.http import HttpResponse,  HttpResponseBadRequest
from django.views.generic import UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from .models import Membership, Order
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from paytm import checksum
merchant_key = '5N1ZW7zBgXCoOiRZ'


def target(request):
    if request.user.is_authenticated:
        return redirect("profile")
    else:
        return redirect("login")


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = "Activate your account."
            message = render_to_string('accounts/acc_activate_email.html',
                                       {
                                           'user':user,
                                           'domain': current_site.domain,
                                           'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                                           'token' : account_activation_token.make_token(user)
                                       })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return render(request, "accounts/verify_email.html", )
    else:
        form = UserRegisterForm()
    context = {
        "form" : form
    }
    return render(request, 'accounts/register.html', context )


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active =True
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        messages.success(request, f"{user.username} Your account has been activated.")
        return redirect("profile")
    else:
        return HttpResponse('Activation link is invalid!')



@login_required
def profile(request):
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f" Your account has been modified.")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {
        "u_form":u_form,
        "p_form":p_form,
        "game":request.user.membership_set.all()[0] if len(request.user.membership_set.all())>0 else None,
        "games":request.user.membership_set.all()[1:] if len(request.user.membership_set.all())>0 else None
    }
    return render(request, "accounts/profile.html", context)


class UpdateSubscription(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "tourney/update_subscription.html"
    model = Membership
    fields = ["user_name", "user_id"]

    def get_object(self):
        id = self.kwargs.get("pk")
        return get_object_or_404(Membership, pk=id)

    def test_func(self):
        membership = self.get_object()
        if self.request.user == membership.player:
            return True
        return False


class DeleteSubscription(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    template_name = "tourney/delete_subscription.html"
    model = Membership

    def get_object(self):
        id = self.kwargs.get("pk")
        return get_object_or_404(Membership, pk=id)

    def get_success_url(self):
        return reverse("profile")

    def test_func(self):
        membership = self.get_object()
        if self.request.user == membership.player:
            return True
        return False


def money_transfer(request):
    if request.method == "POST":
        form = AmountTransfer(request.POST)
        balance = request.user.profile.account_balance
        print(balance)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user

            if request.POST.get("toggle_option") == "withdraw":
                if form.cleaned_data["amount"]>balance:
                    messages.error(request,"You don't have enough balance in your wallet")
                    return render(request, "accounts/transfer.html", {"form":form})
                order.transaction_type = "withdraw"
                order.save()
                obj = request.user.profile
                obj.account_balance -= int(form.data['amount'])
                request.user.profile.save()
            elif request.POST.get("toggle_option") == "deposit":
                order.transaction_type = "deposit"
                order.save()
                params = {
                    "MID": "eJvkxV73534228896310",
                    "ORDER_ID": str(order.order_id),
                    "CUST_ID": request.user.email,
                    "TXN_AMOUNT": str(order.amount),
                    "CHANNEL_ID": "WEB",
                    "INDUSTRY_TYPE_ID": "Retail",
                    "WEBSITE": "WEBSTAGING",
                    'CALLBACK_URL': 'http://13.127.178.253/accounts/profile/trans-status'
                }
                params["CHECKSUMHASH"] = checksum.generate_checksum(params, merchant_key)
                return render(request, "accounts/paytm.html", {"params": params})
            else:
                return HttpResponseBadRequest(content="Invalid Request")
    form = AmountTransfer(initial={"user":request.user})
    context = {
    'form':form
    }
    return render(request, "accounts/transfer.html", context)


@csrf_exempt
def trans_status(request):
    if request.method != "POST":
        return HttpResponseBadRequest(content="<h1>Bad request 400</h1> <br/>invalid request")
    form = request.POST
    response = {}

    for i in form.keys():
        response[i] = form[i]
    code = checksum.verify_checksum(response, merchant_key, form['CHECKSUMHASH'])

    order = Order.objects.get(pk=form["ORDERID"])

    if not code:
        return HttpResponseBadRequest(content="Transaction failed due to Hash missmatch")
    elif form['RESPCODE'] == '01':
        order.transaction_success = True
        order.user.profile.account_balance += order.amount
        order.user.profile.save()
        order.save()

    else:
        return HttpResponse("unkown error contact us")
    return render(request, "accounts/payment_status.html", response)
