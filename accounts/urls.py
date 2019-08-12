from . import views
from django.urls import path
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("", views.target),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name = "accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name = "accounts/logout.html"), name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"), name="password_reset"),
    path("password-reset/done", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("profile/", views.profile, name="profile"),
    path("Money-requests/", views.MoneyRequests.as_view(), name="money_req"),
    path("Money-requests/handle", views.money_req_handle, name="money_req_handle"),
    path("profile/image-upload", views.image_upload, name="image_upload"),
    path("profile/update-info/<int:pk>/", views.UpdateSubscription.as_view(), name="update_subscription"),
    path("profile/update-info/<int:pk>/delete", views.DeleteSubscription.as_view(), name="delete_subscription"),
    path("profile/transfer", views.money_transfer, name= "transfer"),
    path("profile/trans-status", views.trans_status, name="trans_status")
]
