from django.db import models
from django.db.models import CharField
import re
#from django.urls import reverse
from django.core.validators import MaxValueValidator#, validate_comma_separated_integer_list
from django.utils.translation import gettext_lazy as _

class CategoryManager(models.Manager):

    def new_category(self, category):
        new_category = self.create(category=re.sub('\s+', '-', category).lower())

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
    Classe base para as questões
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

class Answer(models.Model):
    question = models.ForeignKey(MultiChoiceQuestion, 
                                 verbose_name=_("Questão"), 
                                 on_delete=models.CASCADE)

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Insira o texto da alternativa que será exibido."),
                               verbose_name=_("Alnternativa"))

    is_correct = models.BooleanField(blank=False,
                                  default=False,
                                  help_text=_("Esta é a resposta correta?"),
                                  verbose_name=_("Correta"))

    def __str__(self):
        return self.content