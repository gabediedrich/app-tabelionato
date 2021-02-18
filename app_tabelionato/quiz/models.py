import random

from django.db import models
from django.db.models import Model
from django.db.models.aggregates import Count
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import re
from random import randint

# Abstract Base Class: Metaclasse para classes abstratas
# e Decoration para definir um método como abstrato
from abc import ABCMeta, abstractmethod

from model_utils.managers import InheritanceManager


class CategoryManager(models.Manager):
    def clean_word(self, word):
        PT_CHARS = {
            'à': 'a',
            'á': 'a',
            'â': 'a',
            'ã': 'a',
            'ò': 'o',
            'ó': 'o',
            'ô': 'o',
            'õ': 'o',
            'è': 'e',
            'é': 'e',
            'ê': 'e',
            'ì': 'i',
            'í': 'i',
            'ù': 'u',
            'ú': 'u',
            'ñ': 'n',
            'ç': 'c',
            '_': '-',
        }
        self.word = word.lower()
        if self.word in PT_CHARS:
            return PT_CHARS[self.word]
        else:
            return self.word

    def new_category(self, category):
        new_category = self.create(category=re.sub('\W', clean_word, category).lower())

        new_category.save()
        return new_category


class Category(models.Model):
    category = models.CharField(
        verbose_name=_('Categoria'),
        max_length=250,
        blank=True,
        unique=True,
        null=True
    )

    objects = CategoryManager()

    def __str__(self):
        return self.category


class Question(models.Model):
    '''
    Classe base para as questões, contém os
    elementos básicos de uma questão
    '''

    # Permite selecionar os métodos filhos durante a execução
    # sem ter que implementar manualmente
    objects = InheritanceManager()

    category = models.ForeignKey(
        Category,
        verbose_name=_('Categoria'),
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
        help_text=_('Insira a dificuldade da questão, entre 1 e 5'),
        verbose_name=_('Dificuldade'),
        validators=[MaxValueValidator(5), MinValueValidator(1)]
    )

    content = models.TextField(
        max_length=500,
        blank=False,
        help_text=_('Insira o enunciado que deve ser exibido.'),
        verbose_name=_('Questão'),
    )

    explanation = models.TextField(
        max_length=500,
        blank=True,
        help_text=_('Explicação que deve ser exibida após a questão ser respondida.'),
        verbose_name=_('Explicação'),
    )

    def get_question(question_id):
        if type(question_id) is int:
            return Question.objects.get_subclass(id=question_id)
        else:
            raise TypeError(_('question_id deve ser do tipo <int>, e não {0}'.format(type(question_id))))

    def get_random_question():
        size = Question.objects.count()
        random_question = None

        while not isinstance(random_question, Question):
            random_id = random.randint(1, size)
            try:
                random_question = Question.objects.filter(id=random_id).select_subclasses().first()
            except Question.DoesNotExist:
                pass

        return random_question

    @abstractmethod
    def check_answer(self, guess):
        raise NotImplementedError

    @abstractmethod
    def get_answer_list(self):
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
    '''
    Classe para questões de múltipla escolha
    '''

    def check_answer(self, guess):
        if type(guess) is int:
            return ClosedAnswer.objects.get(id=guess).is_correct
        else:
            raise TypeError(_('guess deve ser do tipo <int>, e não {0}'.format(type(guess))))

    def _randomize_order(self, queryset):
        return queryset.order_by('?')

    def get_correct_answer(self):
        return ClosedAnswer.objects.filter(question=self, is_correct=True)

    def get_answer_list(self):
        return [
            (answer.id, answer.content)
            for answer in self._randomize_order(ClosedAnswer.objects.filter(question=self))
        ]

    def answer_choice_to_string(self, guess):
        if type(guess) is int:
            return Answer.objects.get(id=guess).content
        else:
            raise TypeError(_('guess deve ser do tipo <int>, e não {0}'.format(type(guess))))


class TrueFalseQuestion(Question):
    '''
    Classe para questões de verdadeiro ou false,
    não possui uma classe <Answer> equivalente
    '''
    is_correct = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_('Correto'),
        help_text=_(
            'Marque se o enunciado for verdadeiro. Deixe em branco se for falso.'
        ),
    )

    def check_answer(self, guess):
        if guess == self.is_correct:  # Funciona com True/False e 1/0
            return True
        else:
            return False

    def get_answer_list(self):
        return [(1, True), (0, False)]

    def get_correct_answer(self):
        return self.is_correct

    def answer_choice_to_string(self, guess):
        return str(guess is True)

    def __str__(self):
        return self.content


class Answer(models.Model):
    '''
    Modelo base de resposta, não há alternativa
    correta.
    '''

    # Permite selecionar os métodos filhos durante a execução
    # sem ter que implementar manualmente
    objects = InheritanceManager()

    content = models.CharField(
        max_length=1000,
        blank=False,
        help_text=_('Insira o texto da alternativa que será exibido.'),
        verbose_name=_('Alternativa'),
    )

    # TODO Adicionar validador

    def __str__(self):
        return self.content


class ClosedAnswer(Answer):
    '''
    Resposta alternativa, é ou verdadeira ou falsa
    '''

    question = models.ForeignKey(
        MultiChoiceQuestion,
        verbose_name=_('Questão'),
        on_delete=models.CASCADE
    )

    is_correct = models.BooleanField(
        blank=False,
        default=False,
        help_text=_('Esta é a resposta correta?'),
        verbose_name=_('Correta'),
    )

    # TODO Adicionar validador

    def __str__(self):
        return self.content + str(self.is_correct)


#
# As classes abaixo estão declaradas, mas
# não serão implementadas até
# eventual surgimento de necessidade
#
class EssayQuestion(Question):
    '''
    Classe para questões de desenvolvimento,
    seja texto ou envio de arquivo
    '''
    pass


class EssayAnswer(Answer):
    '''
    Resposta de desenvolvimento de texto,
    ao contrário dos outros modelos, um objeto desta
    classe será gerado com a entrada usuário que estiver
    respondendo a pergunta, e será salvo para
    avaliação posterior.
    '''
    pass


class FileAnswer(Answer):
    '''
    Tesposta onde deve ser enviado um
    arquivo (pdf, jpg, doc, mp3, mp4, etc...)
    '''


class AnswerEvaluation(models.Model):
    '''
    Classe da avaliação de uma resposta,
    especificamente <EssayAnswer> e <FileAnswer>
    '''
    # Possivelmente engloba
    # avaliador, avaliação,  hora da avaliação,
    # comentário do avaliador


class Quiz(models.Model):
    '''
    Protótipo, atual:
    Gera um quiz com um grupo aleatório de questões,
    Definitivo:
    ?
    '''

    def __init__(self, **kwargs):
        """
        :param kwargs:
            category_list= ('category')
                lista de categorias, a quantia de questões será aleatória
            category_dic= {'str:category' : 'int:number of questions'}
                dicionário de categorias com a quantia de questões desejadas,
                limitado ao total de questões disponíveis na mesma
            question_quantity= int
                total de questões no quiz
            min_difficulty= int
                dificuldade mínima
            max_difficulty= int
                dificuldade máxima
            save= bool
                salvar questionário
                :return quiz_id:
            quiz_id= int
                busca o questionário com o quiz_id, se outro argumento for
                fornecido, o questionário será modificado para corresponder
                às novas regras.
        :return questionnaire:
        """

        if 'question_quantity' in kwargs:
            self.question_quantity = kwargs.get('question_quantity')
        else:
            self.question_quantity = 5

        self.category_list = kwargs.get('category_list')
        self.category_and_quantity_dic = kwargs.get('category_dic')
        self.min_difficulty = kwargs.get('min_difficulty')
        self.max_difficulty = kwargs.get('max_difficulty')
        self.save = kwargs.get('save')
        self.quiz_id = kwargs.get('quiz_id')
        # TODO
        #   Implementar as regras acima
        #

        self.question_list = []
        self.size = 0
        self._populate_questionnaire()

    def _populate_questionnaire(self):
        while len(self.question_list) < self.question_quantity:
            self.question = Question.get_random_question()
            if self.question not in self.question_list:
                self.question_list.append(self.question)

    def get_questionnaire(self):
        return self.question_list
