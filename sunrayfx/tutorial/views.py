from django.shortcuts import render, get_object_or_404

# Create your views here.

from django.views.generic import ListView, DetailView, View
from .models import Tutorial, Lesson
from account.models import UserMembership

class TutorialListView(ListView):
    model = Tutorial
 

class TutorialDetailView(DetailView):
    model = Tutorial
 

class LessonDetailView(View):
    def get(self, request, tutorial_slug, lesson_slug, *args, **kwargs):
        tutorial_qs = Tutorial.objects.filter(slug=tutorial_slug)
        if tutorial_qs.exists():
            tutorial = tutorial_qs.first()

        # lesson = get_object_or_404(Lesson, slug=lesson_slug)

        lesson_qs = Lesson.objects.filter(slug=lesson_slug)
        if lesson_qs.exists():
            lesson = lesson_qs.first()
        


        user_membership = UserMembership.objects.filter(user=request.user).first()
        user_membership_type = user_membership.membership.membership_type

        tutorial_allowed_mem_types = tutorial.allowed_membership.all()

        context = {
            'object':None
        }

        if tutorial_allowed_mem_types.filter(membership_type=user_membership_type).exists():
            context = {'object': lesson}

        return render(request, 'tutorial/lesson_detail.html', context)
