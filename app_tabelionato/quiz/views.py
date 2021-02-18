import random

from django.shortcuts import render
from django.template import Context, Template
from django.template.context_processors import request
import random
from .models import Quiz, Question, Answer, MultiChoiceQuestion, TrueFalseQuestion

import pickle


# Create your views here.

# TODO
#   Criar as funções básicas necessárias de um quiz, notadamente:
#   Sorteio de ordem de questões e respostas;
#   Contagem e Resultado;
#   Temporizador.
#

def QuizTake(request):
    '''
    Protótipo
    Formulário de um quiz, testando as funções
    de um teste anônimo (sem salvar qualquer resultado)
    Uma questão por página
    '''

    # TODO
    #   Dispatcher para assegurar que o usuário está logado
    #   e tem permissão para fazer o quiz
    #
    #   Admin (Mestre/Guru) deve ter a habilidade de visualizar
    #   o teste como um usuário de uma classe inferior?
    #      R: Porque a visualização do teste iria variar?
    #      R: Admin pode ver as repostas corretas

    template_name = 'quiz/question.html'
    result_template_name = 'quiz/result.html'



    if request.method == 'GET':
        request.session['history'] = dict()
        quiz = Quiz()
        question_list = quiz.get_questionnaire()
        current_question = question_list[0]
        question_list = [question.id for question in question_list]
        current_options = current_question.get_answer_list()
        random.shuffle(current_options)
        # Guardar as ordens para manter a ordem na visualização do resultado
        request.session['history'][current_question.id] = current_options

        context = {'question': current_question, 'answers': current_options}
        request.session.set_expiry(1800)  # Expira após 30 minutos
        q_data = {
            'question_list': question_list,
            'current_question': 0,
            'answers': dict(),
            'incorrect_guesses': 0,
            'quiz_score_id': 0
        }

        request.session['q_data'] = q_data
        return render(request, template_name, context)

    elif request.method == 'POST':
        q_data = request.session.__getitem__('q_data')
        q_list = q_data.__getitem__('question_list')
        current_question = Question.get_question(q_list[q_data['current_question']])

        guess = int(request.POST['guess'])
        q_data['answers'][current_question.id] = guess

        if not current_question.check_answer(guess):
            q_data['incorrect_guesses'] += 1

        q_data['current_question'] += 1
        request.session['q_data'] = q_data

        if q_data['current_question'] < len(q_data['question_list']):
            current_question = Question.get_question(q_list[q_data['current_question']])
            current_options = current_question.get_answer_list()
            random.shuffle(current_options)
            request.session['history'][current_question.id] = current_options

            context = {'question': current_question, 'answers': current_options}
            return render(request, template_name, context)
        else:
            question_list = dict()
            for item in q_list:
                question = Question.get_question(item)
                question_list[question.id] = question.content #, question.explanation]

            return render(request, result_template_name, context={'question_list': question_list})


def loadresult(request):
    q_list = request.session.__getitem__('q_data').__getitem__('question_list')
    question_list = dict()
    for item in q_list:
        question = Question.get_question(item)
        question_list[question.id] = question.content

    return render(request, 'quiz/result.html', context={'question_list': question_list})


"""

[10,
 [[1, True], [0, False]],
 6,
 [[19, 'Apenas a I está correta'],
  [21, 'Todas as alternativas estão corretas'],
  [20, 'apenas a III e IV estão corretas'],
  [22, 'Todas as alternativas estão incorretas']],
 1,
 [[1, 'Comunhão universal de bens'],
  [3, 'Separação obrigatória de bens'],
  [4, 'Participação final nos aquestos'],
  [2, 'Separação convencional de bens']],
 9,
 [[1, True], [0, False]],
 2,
 [[6, '60 dias'], [7, '90 dias'], [8, '180 dias'], [5, '30 dias']]]
"""
