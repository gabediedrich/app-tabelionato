from django.contrib import admin

from .models import Category, Question, CategoryManager, \
                    MultiChoiceQuestion, Answer

# Register your models here.
#admin.site.register()
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(MultiChoiceQuestion)
admin.site.register(Answer)