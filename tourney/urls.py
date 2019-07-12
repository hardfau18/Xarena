from django.urls import path
from . import views


urlpatterns = [
    path("store", views.Store.as_view(), name="store"),
    path("game/<int:pk>/", views.Detail.as_view(), name="detail"),
    path("game/<int:pk>/subscribe", views.Subscribe.as_view(), name="subscribe"),
    path("", views.Tourney.as_view(), name = "tournaments"),
    path("<int:pk>/", views.tourney_detail, name="tournament_detail"),
]