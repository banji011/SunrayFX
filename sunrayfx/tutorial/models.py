from django.db import models
from django.urls import reverse
from django.utils import timezone
from account.models import Membership

class Tutorial(models.Model):
    slug = models.SlugField()
    title =  models.CharField(max_length=120)
    description = models.TextField()
    instructor = models.CharField(max_length=150, default='Leye Sunray')
    instructor_thumbnail = models.ImageField(default='avatar.jpg')
    allowed_membership = models.ManyToManyField(Membership)


    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse('tutorials:detail', kwargs={'slug': self.slug})

    @property
    def lessons(self):
        return self.lesson_set.all().order_by('position')

class Lesson(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=120)
    description = models.TextField(default='Lorem Ipsum')
    tutorial = models.ForeignKey(Tutorial, on_delete=models.SET_NULL, null = True)
    position = models.IntegerField()
    video_url = models.CharField(max_length=200)
    video_thumbnail = models.ImageField()
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tutorial:lesson-detail', kwargs= {
            'tutorial_slug': self.tutorial.slug,
            'lesson_slug': self.slug
        })