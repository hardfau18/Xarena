from django.urls import path
from . import views


urlpatterns = [
    path("store/", views.Store.as_view(), name="store"),
    path("game/<int:pk>/", views.Detail.as_view(), name="detail"),
    path("game/<int:pk>/subscribe", views.Subscribe.as_view(), name="subscribe"),
    path("", views.Tourney.as_view(), name = "tournaments"),
    path("/upcoming/<int:pk>/", views.tourney_detail, name="tournament_detail"),
    path("live-tournaments/<int:pk>/", views.live_tourney, name="live_tourney"),
    path("live-tournaments/<int:pk>/manage", views.tourney_manage, name="tourney_manage"),
    path("results/<int:pk>/", views.tourney_results, name="tournament_result")

]
