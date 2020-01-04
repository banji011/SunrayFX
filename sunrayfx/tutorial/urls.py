from django.urls import path
from .views import TutorialListView, TutorialDetailView, LessonDetailView
 

app_name = 'tutorial'

urlpatterns = [
    path('', TutorialListView.as_view(), name='list'),
    path('<slug>', TutorialDetailView.as_view(), name='detail'),
    path('<tutorial_slug>/<lesson_slug>', LessonDetailView.as_view(), name='lesson-detail'),
]


