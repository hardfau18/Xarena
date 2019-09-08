from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, AmountWithdrawForm, PaymentNumForm, AmountDepositForm
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
from .models import Membership, Order,ReqMoneyBack, PaymentNumber, PaymentWindow
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from paytm import checksum
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist



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

        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid() :
            u_form.save()
            p_form.save()
            messages.success(request, f" Your account has been modified.")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    payment = {}
    for i in PaymentWindow.objects.all():
        payment[i] = PaymentNumForm(instance=PaymentNumber.objects.get(user=request.user.profile,
                                                                          payment_window=i) if PaymentNumber.objects.filter(
            user=request.user.profile, payment_window=i).exists() else None)

    context = {
        "payments": payment,
        "u_form":u_form,
        "p_form":p_form,
        "game":request.user.membership_set.all()[0] if len(request.user.membership_set.all())>0 else None,
        "games":request.user.membership_set.all()[1:] if len(request.user.membership_set.all())>0 else None
    }

    return render(request, "accounts/profile.html", context)

def payment_update(request,pk):
    if request.method == "POST":
        pw = get_object_or_404(PaymentWindow, pk=pk)
        form = PaymentNumForm(request.POST, instance= PaymentNumber.objects.get(user=request.user.profile,
            payment_window=pw) if PaymentNumber.objects.filter(user=request.user.profile, payment_window=pw).exists() else None)
        print(form.data)
        if form.is_valid():
            num = form.save(commit=False)
            num.user = request.user.profile
            num.payment_window = pw
            num.save()
            return redirect("profile")
        return redirect("profile")
    return HttpResponseBadRequest(content="Invalid Request")

@login_required
def image_upload(request):
    if request.method =="POST":
        image = ProfileUpdateForm(request.POST, request.FIles, instance=request.user.profile)
        if image.is_valid():
            image.save()
            messages.success(request,"Image has been changed")
            return redirect("profile")


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
        balance = request.user.profile.wallet_balance
        form = AmountWithdrawForm(request.POST, inst=request.user)
        print(form)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            if "payment_method" in form.data:
                try:
                    if balance < req.amount :
                        messages.error(request, "You don't have enough balance in your wallet")
                        return redirect("transfer")
                    req.payment_window = PaymentWindow.objects.get(pk=form.data.get("payment_method"))
                    num=request.user.profile.paymentnumber_set.get(payment_window=req.payment_window).num
                    if num:
                        req.pay_to = num
                    else:
                        return HttpResponseBadRequest(content="<h1>Bad request 400</ha> <br/> invalid request")
                    req.save()
                    messages.success(request, "Your request for payment is success and payment is done soon")
                    return redirect("profile")
                except ObjectDoesNotExist :
                    return HttpResponseBadRequest(content= "<h1> bad request object doesnot exists")
            else:
                messages.error(request, "select valid payment option")
                return redirect("transfer")

    context={
        "withdraw_form" : AmountWithdrawForm(inst=request.user),
        "deposit_form" : AmountDepositForm()
    }
    return render(request, "accounts/transfer.html", context)

def to_wallet(request):
    if request.method != "POST":
        return  HttpResponseBadRequest(content="<h1>Bad request 400</ha> <br/> invalid request")
    form = AmountDepositForm(request.POST)
    try:
        if form.is_valid():
            order = form.save(commit=False)
            order.user=request.user
            order.save()
            params = {
                            "MID": settings.MID,
                            "ORDER_ID": str(order.order_id),
                            "CUST_ID": request.user.email,
                            "TXN_AMOUNT": str(order.amount),
                            "CHANNEL_ID": "WAP",
                            "INDUSTRY_TYPE_ID": "Retail",
                            "WEBSITE": "WEBSTAGING",
                            'CALLBACK_URL': 'http://www.xarena.cf/accounts/profile/trans-status'
                        }
            params["CHECKSUMHASH"] = checksum.generate_checksum(params, settings.MERCHANT_KEY)
            return render(request, "accounts/paytm.html", {"params": params})
        else:
            return HttpResponseBadRequest(content="Invalid Request")
    except:
        pass

@csrf_exempt
def trans_status(request):
    if request.method != "POST":
        return HttpResponseBadRequest(content="<h1>Bad request 400</h1> <br/>invalid request")
    form = request.POST
    response = {}

    for i in form.keys():
        response[i] = form[i]
    code = checksum.verify_checksum(response, settings.MERCHANT_KEY, form['CHECKSUMHASH'])

    order = Order.objects.get(pk=form["ORDERID"])

    if not code:
        return HttpResponseBadRequest(content="Transaction failed due to Hash missmatch")
    elif form['RESPCODE'] == '01':
        order.transaction_success = True
        order.user.profile.wallet_balance += order.amount
        order.user.profile.save()
        order.save()

    else:
        return HttpResponse("unkown error contact us")
    return render(request, "accounts/payment_status.html", response)

@method_decorator(staff_member_required, name="dispatch")
class MoneyRequests(ListView):
    template_name = "accounts/money-requests.html"
    paginate_by = 10
    queryset = ReqMoneyBack.objects.filter(trans_status=False)


@staff_member_required
def money_req_handle(request):
    if request.method=="POST":
        req=get_object_or_404(ReqMoneyBack,pk=request.POST.get("id"))
        req.trans_status = True
        req.save()
        messages.success(request,f"transaction on order {req.pk} is success.")
        return redirect("money_req")
    else:
        return HttpResponseBadRequest()




