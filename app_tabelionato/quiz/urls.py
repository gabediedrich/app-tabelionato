from django.urls import path

from .views import QuizTake, loadresult
app_name = 'quiz'

urlpatterns = [
    path('take/', view=QuizTake, name='quiztake'),
    path('load/', view=loadresult, name='loadresult'),
]
