import re, json
from datetime import datetime, timezone
from django.db import models
from django.db.models import Model
from django.db.models.aggregates import Count
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    validate_comma_separated_integer_list,
    ValidationError,
)

from random import randint, random
from model_utils.managers import InheritanceManager
from tabelionato.utils.text_utils import remove_accents

# Abstract Base Class: Metaclasse para classes abstratas
# e Decoration para definir um método como abstrato
from abc import ABCMeta, abstractmethod


class CategoryManager(models.Manager):
    def new_category(self, category):
        new_category = self.create(
            category=re.sub("\W", remove_accents, category).lower()
        )

        new_category.save()
        return new_category


class Category(models.Model):
    category = models.CharField(
        verbose_name=_("Categoria"), max_length=250, blank=True, unique=True, null=True
    )

    objects = CategoryManager()

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.category


class Quiz(models.Model):
    title = models.CharField(verbose_name=_("Título"), max_length=60, blank=False)

    description = models.TextField(
        verbose_name=_("Descrição"),
        help_text=_("Uma descrição breve do Quiz"),
        blank=True,
        max_length=150,
    )

    url = models.SlugField(
        verbose_name=_("URL amigável"),
        max_length=60,
        blank=False,
    )

    category = models.ForeignKey(
        Category,
        verbose_name=_("Categoria"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    random_order = models.BooleanField(
        verbose_name=_("Ordem Aleatória"),
        help_text=_(
            "Se sim, as perguntas serão dispostas" " de forma aleatória par o usuário."
        ),
        blank=False,
        default=False,
    )

    max_questions = models.PositiveIntegerField(
        verbose_name=_("Número de questões"),
        help_text=_("Número máximo de questões a" " a serem feitas a cada tentativa"),
        blank=True,
        null=True,
    )

    answers_at_end = models.BooleanField(
        verbose_name=_("Exibir respostas no final"),
        help_text=_(
            "Se sim, o usuário poderá ver"
            " ver as respostas marcadas"
            " após responder o questionário."
        ),
        blank=False,
        default=True,
    )

    store_result = models.BooleanField(
        verbose_name=_("Guardar resultado"),
        help_text=_(
            "Se sim, o resultado de cada" " tentativa do usuário" " será armazenado."
        ),
        blank=False,
        default=True,
    )

    single_attempt = models.BooleanField(
        verbose_name=_("Tentativa Única"),
        help_text=_(
            "Se sim, cada usuário só" " poderá responder o questionário" " uma vez."
        ),
        blank=False,
        default=False,
    )

    pass_mark = models.SmallIntegerField(
        verbose_name=_("Pontuação Mínima"),
        help_text=_("A pontuação necessária para ser aprovado"),
        blank=True,
        default=0,
        validators=[MaxValueValidator(100)],
    )

    success_text = models.TextField(
        verbose_name=_("Texto de sucesso"),
        help_text=_("Exibido se o usuário atinge" " a pontuação mínima"),
        blank=True,
    )

    fail_text = models.TextField(
        verbose_name=_("Texto de falha"),
        help_text=_("Exibido se o usuário NÃO atinge" " a pontuação mínima"),
        blank=True,
    )

    draft = models.BooleanField(
        verbose_name=_("Rascunho"),
        help_text=_(
            "Se sim, o quiz não será exibido"
            " para os usuários e somente"
            " poderá ser feito por editores."
        ),
        blank=True,
        default=True,
    )

    date_added = models.DateTimeField(_("Data de Criação"), auto_now_add=True)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        # self.url = remove_accents(self.url)
        self.url = re.sub("\s+", "-", self.url).lower()

        self.url = "".join(
            letter for letter in self.url if letter.isalnum() or letter == "-"
        )

        if self.single_attempt is True:
            self.store_result = True

        if self.pass_mark > 100:
            raise ValidationError("%s está acima de 100" % self.pass_mark)

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = _("Questionário")
        verbose_name_plural = _("Questionários")

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    def anon_score_id(self):
        return str(self.id) + "_score"

    def anon_q_list(self):
        return str(self.id) + "_q_list"

    def anon_q_data(self):
        return str(self.id) + "_data"


class Question(models.Model):
    """
    Classe base para as questões, contém os
    elementos básicos de uma questão
    """

    # Permite selecionar os métodos filhos durante a execução
    # sem ter que implementar manualmente

    objects = InheritanceManager()

    category = models.ForeignKey(
        Category,
        verbose_name=_("Categoria"),
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    # Dificuldade de uma questão, poderá ser
    # utilizado para nivelamento e ser automaticamente
    # atualizado pelo app

    difficulty = models.IntegerField(
        default=1,
        blank=True,
        help_text=_("Insira a dificuldade da questão, entre 1 e 5"),
        verbose_name=_("Dificuldade"),
        validators=[MaxValueValidator(5), MinValueValidator(1)],
    )

    content = models.TextField(
        max_length=500,
        blank=False,
        help_text=_("Insira o enunciado que deve ser exibido."),
        verbose_name=_("Questão"),
    )

    explanation = models.TextField(
        max_length=500,
        blank=True,
        help_text=_("Explicação que deve ser exibida após a questão ser respondida."),
        verbose_name=_("Explicação"),
    )

    quiz = models.ManyToManyField(
        Quiz,
        verbose_name=_("Quiz"),
        blank=True,
    )

    def get_question(self, question_id):
        if type(self.question_id) is int:
            return Question.objects.get_subclass(id=self.question_id)
        else:
            raise TypeError(
                _(
                    "question_id deve ser do tipo <int>, e não {0}".format(
                        type(self.question_id)
                    )
                )
            )

    def get_random_question(self):
        size = Question.objects.count()
        random_question = None

        while not isinstance(random_question, Question):
            random_id = random.randint(1, size)
            try:
                random_question = (
                    Question.objects.filter(id=random_id).select_subclasses().first()
                )
            except Question.DoesNotExist:
                pass

        return random_question

    @abstractmethod
    def check_answer(self, guess):
        raise NotImplementedError

    @abstractmethod
    def get_answer_list(self):
        raise NotImplementedError

    def get_answer_list_with_correct(self):
        raise NotImplementedError

    @abstractmethod
    def get_correct_answer(self):
        raise NotImplementedError

    @abstractmethod
    def answer_choice_to_string(self, guess):
        raise NotImplementedError

    def __str__(self):
        return self.content


class MultiChoiceQuestion(Question):
    """
    Classe para questões de múltipla escolha
    """

    def check_answer(self, guess):
        try:
            guess = int(guess)
            return Answer.objects.get(id=guess).is_correct
        except:
            raise TypeError(_("guess deve ser um <int> e não {0}".format(guess)))

    def _randomize_order(self, queryset):
        return queryset.order_by("?")

    def get_correct_answer(self):
        return Answer.objects.filter(question=self, is_correct=True)

    def get_answer_list(self):
        return [
            (answer.id, answer.content)
            for answer in list(Answer.objects.filter(question=self))
        ]

    def get_answer_list_with_correct(self):
        return [
            (answer.id, answer.content, answer.is_correct)
            for answer in list(Answer.objects.filter(question=self))
        ]

    def answer_choice_to_string(self, guess):
        try:
            return Answer.objects.get(id=int(guess)).content
        except:
            raise TypeError(
                _("guess deve ser do tipo <int>, e não {0}".format(type(guess)))
            )

    class Meta:
        verbose_name = _("Questão de Múltipla Escolha")
        verbose_name_plural = _("Questões de Múltipla Escolha")

    def __str__(self):
        return self.content[:20]


class TrueFalseQuestion(Question):
    """
    Classe para questões de verdadeiro ou false,
    não possui uma classe <Answer> equivalente
    """

    is_correct = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_("Correto"),
        help_text=_(
            "Marque se o enunciado for verdadeiro. Deixe em branco se for falso."
        ),
    )

    def check_answer(self, guess):
        if guess == self.is_correct:
            return True
        else:
            return False

    def get_answer_list(self):
        return [(1, "Verdadeiro"), (0, "Falso")]

    def get_answer_list_with_correct(self):
        if self.is_correct:
            result = [(1, "Verdadeiro", True), (0, "Falso", False)]
        else:
            result = [(1, "Verdadeiro", False), (0, "Falso", True)]
        return result

    def get_correct_answer(self):
        return self.is_correct

    def answer_choice_to_string(self, guess):
        return str(guess is True)

    class Meta:
        verbose_name = _("Questão de Verdadeiro ou Falso")
        verbose_name_plural = _("Questões de Verdadeiro ou Falso")

    def __str__(self):
        return self.content[:20]


class Answer(models.Model):
    """
    Modelo base de resposta, não há alternativa
    correta.
    """

    objects = InheritanceManager()

    content = models.CharField(
        max_length=1000,
        blank=False,
        help_text=_("Insira o texto da alternativa que será exibido."),
        verbose_name=_("Alternativa"),
    )

    question = models.ForeignKey(
        MultiChoiceQuestion, verbose_name=_("Questão"), on_delete=models.CASCADE
    )

    is_correct = models.BooleanField(
        blank=False,
        default=False,
        help_text=_("Esta é a resposta correta?"),
        verbose_name=_("Correta"),
    )

    # TODO Adicionar validador

    def __str__(self):
        return self.content + ": " + str(self.is_correct)


class AttemptManager(models.Manager):
    def new_attempt(self, user, quiz):
        if quiz.random_order is True:
            question_set = quiz.question_set.all().select_subclasses().order_by("?")
        else:
            question_set = quiz.question_set.all().select_subclasses()

        question_set = [item.id for item in question_set]

        if len(question_set) == 0:
            raise ImproperlyConfigured(
                "Question set of the quiz is empty. "
                "Please configure questions properly"
            )

        if quiz.max_questions and quiz.max_questions < len(question_set):
            question_set = question_set[: quiz.max_questions]

        questions = ",".join(map(str, question_set)) + ","

        new_attempt = self.create(
            user=user,
            quiz=quiz,
            question_order=questions,
            question_list=questions,
            incorrect_questions="",
            current_score=0,
            complete=False,
            user_answers="{}",
        )
        return new_attempt

    def user_attempt(self, user, quiz):
        if (
            quiz.single_attempt is True
            and self.filter(user=user, quiz=quiz, complete=True).exists()
        ):

            return False

        try:
            attempt = self.get(user=user, quiz=quiz, complete=False)
        except Attempt.DoesNotExist:
            attempt = self.new_attempt(user, quiz)
        except Attempt.MultipleObjectsReturned:
            attempt = self.filter(user=user, quiz=quiz, complete=False)[0]
        return attempt


class Attempt(models.Model):
    """
    Used to store the progress of logged in users attempt a quiz.
    Replaces the session system used by anon users.
    Question_order is a list of integer pks of all the questions in the
    quiz, in order.
    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.
    Incorrect_questions is a list in the same format.
    Attempt deleted when quiz finished unless quiz.exam_paper is true.
    User_answers is a json object in which the question PK is stored
    with the answer the user gave.
    """

    user = models.ForeignKey(
        get_user_model(), verbose_name=_("User"), on_delete=models.CASCADE
    )

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"), on_delete=models.CASCADE)

    question_order = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024,
        verbose_name=_("Question Order"),
    )

    question_list = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024,
        verbose_name=_("Question List"),
    )

    incorrect_questions = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024,
        blank=True,
        verbose_name=_("Incorrect questions"),
    )

    current_score = models.IntegerField(verbose_name=_("Current Score"))

    complete = models.BooleanField(
        default=False, blank=False, verbose_name=_("Complete")
    )

    user_answers = models.TextField(
        blank=True, default="{}", verbose_name=_("User Answers")
    )

    start = models.DateTimeField(auto_now_add=True, verbose_name=_("Start"))

    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    objects = AttemptManager()

    class Meta:
        permissions = (("view_attempts", _("Can see completed exams.")),)

    def get_first_question(self):
        """
        Returns the next question.
        If no question is found, returns False
        Does NOT remove the question from the front of the list.
        """
        if not self.question_list:
            return False

        first, _ = self.question_list.split(",", 1)
        question_id = int(first)
        return Question.objects.get_subclass(id=question_id)

    def remove_first_question(self):
        if not self.question_list:
            return

        _, others = self.question_list.split(",", 1)
        self.question_list = others
        self.save()

    def add_to_score(self, points):
        self.current_score += int(points)
        self.save()

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(",") if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0  # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = datetime.now(timezone.utc)
        self.save()

    def add_incorrect_question(self, question):
        """
        Adds uid of incorrect question to the list.
        The question object must be passed in.
        """
        if len(self.incorrect_questions) > 0:
            self.incorrect_questions += ","
        self.incorrect_questions += str(question.id) + ","
        if self.complete:
            self.add_to_score(-1)
        self.save()

    @property
    def get_incorrect_questions(self):
        """
        Returns a list of non empty integers, representing the pk of
        questions
        """
        return [int(q) for q in self.incorrect_questions.split(",") if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ",".join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return self.quiz.success_text
        else:
            return self.quiz.fail_text

    def add_user_answer(self, question, guess):
        current = json.loads(self.user_answers)
        current[question.id] = guess
        self.user_answers = json.dumps(current)
        self.save()

    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()
        questions = sorted(
            self.quiz.question_set.filter(id__in=question_ids).select_subclasses(),
            key=lambda q: question_ids.index(q.id),
        )

        if with_answers:
            user_answers = json.loads(self.user_answers)
            for question in questions:
                question.user_answer = user_answers[str(question.id)]

        return questions

    @property
    def questions_with_user_answers(self):
        return {q: q.user_answer for q in self.get_questions(with_answers=True)}

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        answered = len(json.loads(self.user_answers))
        total = self.get_max_score
        return answered, total


class ProgressManager(models.Manager):
    def new_progress(self, user):
        new_progress = self.create(user=user, score="")
        new_progress.save()
        return new_progress


class Progress(models.Model):
    user = models.OneToOneField(
        get_user_model(), verbose_name=_("Usuário"), on_delete=models.CASCADE
    )

    score = models.CharField(
        validators=[validate_comma_separated_integer_list],
        max_length=1024,
        verbose_name=_("Pontuação"),
    )

    quiz = models.ForeignKey(
        Quiz, verbose_name=_("Questionário"), on_delete=models.CASCADE, null=True
    )

    correct_answer = models.CharField(
        max_length=10, verbose_name=_("Respostas Corretas")
    )

    wrong_answer = models.CharField(
        max_length=10, verbose_name=_("Respostas Incorretas")
    )

    objects = ProgressManager()

    class Meta:
        verbose_name = _("Progresso do Usuário")
        verbose_name_plural = _("Progressos dos Usuários")

    @property
    def list_all_cat_scores(self):
        """
        Returns a dict in which the key is the category name and the item is
        a list of three integers.
        The first is the number of questions correct,
        the second is the possible best score,
        the third is the percentage correct.
        The dict will have one key for every category that you have defined
        """
        score_before = self.score
        output = {}

        for cat in Category.objects.all():
            to_find = re.escape(cat.category) + r",(\d+),(\d+),"
            #  group 1 is score, group 2 is highest possible

            match = re.search(to_find, self.score, re.IGNORECASE)

            if match:
                score = int(match.group(1))
                possible = int(match.group(2))

                try:
                    percent = int(round((float(score) / float(possible)) * 100))
                except:
                    percent = 0

                output[cat.category] = [score, possible, percent]

            else:
                self.score += cat.category + ",0,0,"
                output[cat.category] = [0, 0]

        if len(self.score) > len(score_before):
            self.save()

        return output

    def update_score(self, question, score_to_add=0, possible_to_add=0):
        category_test = Category.objects.filter(category=question.category).exists()

        if any(
            [
                item is False
                for item in [
                    category_test,
                    score_to_add,
                    possible_to_add,
                    isinstance(score_to_add, int),
                    isinstance(possible_to_add, int),
                ]
            ]
        ):
            return _("error"), _("A categoria não existe ou a pontuação está incorreta")

        to_find = (
            re.escape(str(question.category)) + r",(?P<score>\d+),(?P<possible>\d+),"
        )

        match = re.search(to_find, self.score, re.IGNORECASE)

        if match:
            updated_score = int(match.group("score")) + abs(score_to_add)
            updated_possible = int(match.group("possible")) + abs(possible_to_add)

            new_score = ",".join(
                [str(question.category), str(updated_score), str(updated_possible), ""]
            )

            self.score = self.score.replace(match.group(), new_score)
            self.save()

        else:
            self.score += ",".join(
                [str(question.category), str(score_to_add), str(possible_to_add), ""]
            )
            self.save()

    def show_exams(self):
        return Attempt.objects.filter(user=self.user, complete=True).order_by("-start")

    def __str__(self):
        return self.user.username + " - " + self.score
