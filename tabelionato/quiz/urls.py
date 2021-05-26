from django.urls import path
from django.views.generic import RedirectView
from .views import (
    QuizListView,
    QuizDetailView,
    CategoryListView,  # CategoryDetailView,
    # QuizMarkingList, QuizMarkingDetail,
    # quizUserProgressView,
    QuizTake,
)

app_name = "quiz"

urlpatterns = [
    path("list/", view=QuizListView.as_view(), name="quiz_list"),
    path("<slug:quiz_url>/", RedirectView.as_view(url="detail")),
    path("<slug:quiz_url>/detail/", view=QuizDetailView.as_view(), name="quiz_detail"),
    path("<slug:quiz_url>/take/", view=QuizTake.as_view(), name="quiz_take"),
    path("categoria/index/", view=CategoryListView, name="category_index"),
    # path("categoria/<slug:category_name>/", view=CategoryDetailView.as_view(), name="category_detail"),
    # path("pontuacao/", view=QuizMarkingList.as_view(), name="quiz_marking_list"),
    # path("pontuacao/<slug:attempt>/", view=QuizMarkingDetail.as_view(), name="quiz_marking_detail"),
    # path("/", view=.as_view(), name=""),
]
