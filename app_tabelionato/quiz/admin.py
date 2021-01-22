from django.contrib import admin
from django import forms


from .models import Category, \
                    Question,  MultiChoiceQuestion, \
                    TrueFalseQuestion, Answer, ClosedAnswer

# Register your models here.
#admin.site.register()
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(MultiChoiceQuestion)
admin.site.register(TrueFalseQuestion)
admin.site.register(Answer)
admin.site.register(ClosedAnswer)

# TODO criar classes de cadastro
