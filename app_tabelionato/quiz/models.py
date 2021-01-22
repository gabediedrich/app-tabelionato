from django.db import models
from django.db.models import CharField
import re
#from django.urls import reverse
from django.core.validators import MaxValueValidator#, validate_comma_separated_integer_list
from django.utils.translation import gettext_lazy as _

class CategoryManager(models.Manager):

    def clean_word(word):
        PT_CHARS = {
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o',
            'è': 'e', 'é': 'e', 'ê': 'e',
            'ì': 'i', 'í': 'i',
            'ù': 'u', 'ú': 'u',
            'ñ': 'n', 'ç': 'c', ' ': '-'
        }
        word = word.lower()
        if word in PT_CHARS:
            return PT_CHARS[word.lower()]
        else:
            return '_'

    def new_category(self, category):
        new_category = self.create(category=re.sub('\W', clean_word, category).lower())

        new_category.save()
        return new_category

class Category(models.Model):

    category = models.CharField(
        verbose_name=_("Categoria"),
        max_length=250, blank=True,
        unique=True, null=True)

    objects = CategoryManager()

    def __str__(self):
        return self.category

class Question(models.Model):
    """
    Classe base para as questões, contém
    categoria, enunciado e explicação
    """

    category = models.ForeignKey(Category,
                                 verbose_name=_("Categoria"),
                                 blank=True,
                                 null=True,
                                 on_delete=models.CASCADE)

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Insira o enunciado que deve ser exibido "),
                               verbose_name=_('Questão'))

    explanation = models.TextField(max_length=2000,
                                   blank=True,
                                   help_text=_("Explicação que deve ser exibida após "
                                               "a questão ser respondida"),
                                   verbose_name=_('Explicação'))

    def __str__(self):
        return self.content

class MultiChoiceQuestion(Question):
    """
    Classe para questões de múltipla escolha
    """

    def check_if_correct(self, guess):
        answer = Answer.objects.get(id=guess)

        if answer.is_correct is True:
            return True
        else:
            return False

    def randomize_order(self, queryset):
            return queryset.order_by('?')

    def get_answers(self):
        return self.randomize_order(Answer.objects.filter(question=self))

    def get_answers_list(self):
        return [(answer.id, answer.content) for answer in
                self.randomize_order(Answer.objects.filter(question=self))]

    def answer_choice_to_string(self, guess):
        return Answer.objects.get(id=guess).content

class TrueFalseQuestion(Question):

    is_correct = models.BooleanField(blank=False,
                                  default=False,
                                  verbose_name="Correto",
                                  help_text="Marque se o enunciado for verdadeiro. "
                                            "Deixe em branco se for falso."
    )

    def check_answer(self, guess):
        if not isinstance(guess, bool):
            return False

        if guess == self.is_correct:
            return True
        else:
            return False

    def get_answer(self):
        return self.is_correct

    def get_answers_list(self):
        return [(True, True), (False, False)]

    def __str__(self):
        return [
            {'content': self.content,
             'answer': self.is_correct}
        ]

class Answer(models.Model):
    """
    Modelo base de resposta, não há alternativa
    correta.
    """
    question = models.ForeignKey(Question,
                                 verbose_name=_("Questão"),
                                 on_delete=models.CASCADE)

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Insira o texto da alternativa que será exibido."),
                               verbose_name=_("Alternativa"))

    # TODO Adicionar validador

    def __str__(self):
        return self.content

class ClosedAnswer(Answer):
    """
    Modelo de resposta em que a alternativa
    é ou verdadeira ou falsa
    """
    is_correct = models.BooleanField(blank=False,
                                  default=False,
                                  help_text=_("Esta é a resposta correta?"),
                                  verbose_name=_("Correta"))
    # TODO Adicionar validador

    def __str__(self):
        return [
            {'content': self.content,
             'answer': self.is_correct}
        ]

# TODO Modelo de resposta de questão aberta (texto)
# Possivelmente engloba
# user.id, hora do envio,
# avaliação,  hora da avaliação
# avaliador, comentário do avaliador
