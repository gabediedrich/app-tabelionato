from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _


from .models import (
    Quiz,
    Category,
    Question,
    Progress,
    MultiChoiceQuestion,
    TrueFalseQuestion,
    Answer,
)


class AnswerInline(admin.TabularInline):
    model = Answer


class QuizAdminForm(forms.ModelForm):
    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questões"),
        widget=FilteredSelectMultiple(verbose_name=_("Questões"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields[
                "questions"
            ].initial = self.instance.question_set.all().select_subclasses()

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data["questions"])
        self.save_m2m()
        return quiz


class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm

    list_display = ("title", "category", "url")
    list_filter = (
        "category",
        "draft",
    )
    search_fields = (
        "description",
        "category",
    )


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("category",)


class MultiChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "content",
        "category",
    )
    list_filter = ("category",)
    fields = (
        "content",
        "category",
        "explanation",
        "quiz",
    )

    search_fields = (
        "content",
        "category",
        "explanation",
    )
    filter_horizontal = ("quiz",)

    inlines = [AnswerInline]


class TrueFalseQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "content",
        "category",
    )
    list_filter = ("category",)
    fields = (
        "content",
        "is_correct",
        "category",
        "explanation",
        "quiz",
    )

    search_fields = (
        "content",
        "category",
        "explanation",
    )
    filter_horizontal = ("quiz",)


class ProgressAdmin(admin.ModelAdmin):
    # TODO
    search_fields = (
        "user",
        "score",
    )


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(MultiChoiceQuestion, MultiChoiceQuestionAdmin)
admin.site.register(TrueFalseQuestion, TrueFalseQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
