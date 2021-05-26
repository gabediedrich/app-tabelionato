# from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from .forms import QuestionForm
from .models import (
    Quiz,
    Category,
    Progress,
    Attempt,
    Question,
)

import random


class QuizMarkerMixin(object):
    @login_required
    @permission_required("quiz.view_attempts")
    def dispatch(self, *args, **kwargs):
        return super(QuizMarkerMixin, self).dispatch(*args, **kwargs)


class AttemptFilterTitleMixin(object):
    def get_queryset(self):
        queryset = super(AttemptFilterTitleMixin, self).get_queryset()
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)

        return queryset


class QuizListView(ListView):
    model = Quiz
    slug_field = "url"
    slug_url_kwarg = "quiz_url"
    template_name = "quiz/quiz_list.html"


class QuizDetailView(DetailView):
    model = Quiz
    slug_field = "url"
    slug_url_kwarg = "quiz_url"
    template_name = "quiz/quiz_detail.html"

    # @permission_required('quiz.change_quiz')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class CategoryListView(ListView):
    model = Category


class ViewQuizListByCategory(ListView):
    model = Quiz
    template_name = "quiz/view_quiz_category.html"

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, category=self.kwargs["category_name"]
        )

        return super(ViewQuizListByCategory, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self).get_context_data(**kwargs)

        context["category"] = self.category
        return context

    def get_queryset(self):
        queryset = super(ViewQuizListByCategory, self).get_queryset()
        return queryset.filter(category=self.category, draft=False)


@login_required
def quizUserProgressView(request):
    paginate_by = 8
    progress, c = Progress.objects.get_or_create(user=request.user)
    all_exams = progress.show_exams()
    paginator = Paginator(all_exams, paginate_by)
    page = request.GET.get("page")

    try:
        exams_pages = paginator.get_page(page)
    except PageNotAnInteger:
        exams_pages = paginator.page(1)
    except EmptyPage:
        exams_pages = paginator.page(paginator.num_pages)

    context = {"cat_scores": progress.list_all_cat_scores, "exams": exams_pages}

    return render(request, "quiz/progress_list.html", context)


class QuizMarkingList(QuizMarkerMixin, AttemptFilterTitleMixin, ListView):
    model = Attempt

    def get_queryset(self):
        queryset = super(QuizMarkingList, self).get_queryset().filter(complete=True)

        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        return queryset

    class Meta:
        pass


@login_required
class QuizMarkingDetail(QuizMarkerMixin, DetailView):
    model = Attempt

    def post(self, request, *args, **kwargs):
        attempt = self.get_object()

        q_to_toggle = request.POST.get("qid", None)
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in attempt.get_incorrect_questions:
                attempt.remove_incorrect_question(q)
            else:
                attempt.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context["questions"] = context["attempt"].get_questions(with_answers=True)
        return context


# TODO QuizTake de página única, igual a versão anterior,
#      mas utilizando o AttemptManager


class QuizTake(FormView):
    form_class = QuestionForm
    slug_field = "url"
    slug_url_kwarg = "quiz_url"
    template_name = "quiz/question.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, url=self.kwargs["quiz_url"])
        if self.quiz.draft and not request.user.has_perm("quiz.change_quiz"):
            raise PermissionDenied

        self.logged_in_user = self.request.user.is_authenticated

        if self.logged_in_user:
            self.attempt = Attempt.objects.user_attempt(request.user, self.quiz)
        if self.attempt is False:
            return render(request, "quiz/quiz_unavailable.html")

        return super(QuizTake, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=QuestionForm):
        if self.logged_in_user:
            self.question = self.attempt.get_first_question()
            self.progress = self.attempt.progress()
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        return dict(kwargs, question=self.question)

    def form_valid(self, form):
        if self.logged_in_user:
            self.form_valid_user(form)
            if self.attempt.get_first_question() is False:
                return self.final_result_user()
        self.request.POST = {}

        return super(QuizTake, self).get(self, self.request)

    def get_context_data(self, **kwargs):
        context = super(QuizTake, self).get_context_data(**kwargs)
        context["question"] = self.question
        context["quiz"] = self.quiz
        if hasattr(self, "previous"):
            context["previous"] = self.previous
        if hasattr(self, "progress"):
            context["progress"] = self.progress
        return context

    def form_valid_user(self, form):
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data["answers"]
        is_correct = self.question.check_answer(guess)

        if is_correct is True:
            self.attempt.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.attempt.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        if self.quiz.answers_at_end is not True:
            self.previous = {
                "previous_answer": guess,
                "previous_outcome": is_correct,
                "previous_question": self.question,
                "previous_question_id": self.question.id,
                "answers": self.question.get_answers(),
                "question_type": {self.question.__class__.__name__: True},
            }
        else:
            self.previous = {}

        self.attempt.add_user_answer(self.question, guess)
        self.attempt.remove_first_question()

    def final_result_user(self):
        results = {
            "quiz": self.quiz,
            "score": self.attempt.get_current_score,
            "max_score": self.attempt.get_max_score,
            "percent": self.attempt.get_percent_correct,
            "attempt": self.attempt,
            "previous": self.previous,
        }

        self.attempt.mark_quiz_complete()

        if self.quiz.answers_at_end:
            results["questions"] = self.attempt.get_questions(with_answers=True)
            results["incorrect_questions"] = self.attempt.get_incorrect_questions

        if self.quiz.store_result is False:
            self.attempt.delete()

        return render(self.request, "quiz/results.html", results)
