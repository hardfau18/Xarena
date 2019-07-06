from django.urls import path
from . import views


urlpatterns = [
    path("", views.Store.as_view(), name="store"),
    path("game/<int:pk>/", views.Detail.as_view(), name="detail"),
    path("game/<int:pk>/subscribe", views.Subscribe.as_view(), name="subscribe")
]