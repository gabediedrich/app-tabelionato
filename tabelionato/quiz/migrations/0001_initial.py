# Generated by Django 3.1.8 on 2021-05-26 07:36

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(help_text='Insira o texto da alternativa que será exibido.', max_length=1000, verbose_name='Alternativa')),
                ('is_correct', models.BooleanField(default=False, help_text='Esta é a resposta correta?', verbose_name='Correta')),
            ],
        ),
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_order', models.CharField(max_length=1024, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')], verbose_name='Question Order')),
                ('question_list', models.CharField(max_length=1024, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')], verbose_name='Question List')),
                ('incorrect_questions', models.CharField(blank=True, max_length=1024, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')], verbose_name='Incorrect questions')),
                ('current_score', models.IntegerField(verbose_name='Current Score')),
                ('complete', models.BooleanField(default=False, verbose_name='Complete')),
                ('user_answers', models.TextField(blank=True, default='{}', verbose_name='User Answers')),
                ('start', models.DateTimeField(auto_now_add=True, verbose_name='Start')),
                ('end', models.DateTimeField(blank=True, null=True, verbose_name='End')),
            ],
            options={
                'permissions': (('view_attempts', 'Can see completed exams.'),),
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(blank=True, max_length=250, null=True, unique=True, verbose_name='Categoria')),
            ],
            options={
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.IntegerField(blank=True, default=1, help_text='Insira a dificuldade da questão, entre 1 e 5', validators=[django.core.validators.MaxValueValidator(5), django.core.validators.MinValueValidator(1)], verbose_name='Dificuldade')),
                ('content', models.TextField(help_text='Insira o enunciado que deve ser exibido.', max_length=500, verbose_name='Questão')),
                ('explanation', models.TextField(blank=True, help_text='Explicação que deve ser exibida após a questão ser respondida.', max_length=500, verbose_name='Explicação')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.category', verbose_name='Categoria')),
            ],
        ),
        migrations.CreateModel(
            name='MultiChoiceQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='quiz.question')),
            ],
            options={
                'verbose_name': 'Questão de Múltipla Escolha',
                'verbose_name_plural': 'Questões de Múltipla Escolha',
            },
            bases=('quiz.question',),
        ),
        migrations.CreateModel(
            name='TrueFalseQuestion',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='quiz.question')),
                ('is_correct', models.BooleanField(default=False, help_text='Marque se o enunciado for verdadeiro. Deixe em branco se for falso.', verbose_name='Correto')),
            ],
            options={
                'verbose_name': 'Questão de Verdadeiro ou Falso',
                'verbose_name_plural': 'Questões de Verdadeiro ou Falso',
            },
            bases=('quiz.question',),
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=60, verbose_name='Título')),
                ('description', models.TextField(blank=True, help_text='Uma descrição breve do Quiz', max_length=150, verbose_name='Descrição')),
                ('url', models.SlugField(max_length=60, verbose_name='URL amigável')),
                ('random_order', models.BooleanField(default=False, help_text='Se sim, as perguntas serão dispostas de forma aleatória par o usuário.', verbose_name='Ordem Aleatória')),
                ('max_questions', models.PositiveIntegerField(blank=True, help_text='Número máximo de questões a a serem feitas a cada tentativa', null=True, verbose_name='Número de questões')),
                ('answers_at_end', models.BooleanField(default=True, help_text='Se sim, o usuário poderá ver ver as respostas marcadas após responder o questionário.', verbose_name='Exibir respostas no final')),
                ('store_result', models.BooleanField(default=True, help_text='Se sim, o resultado de cada tentativa do usuário será armazenado.', verbose_name='Guardar resultado')),
                ('single_attempt', models.BooleanField(default=False, help_text='Se sim, cada usuário só poderá responder o questionário uma vez.', verbose_name='Tentativa Única')),
                ('pass_mark', models.SmallIntegerField(blank=True, default=0, help_text='A pontuação necessária para ser aprovado', validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Pontuação Mínima')),
                ('success_text', models.TextField(blank=True, help_text='Exibido se o usuário atinge a pontuação mínima', verbose_name='Texto de sucesso')),
                ('fail_text', models.TextField(blank=True, help_text='Exibido se o usuário NÃO atinge a pontuação mínima', verbose_name='Texto de falha')),
                ('draft', models.BooleanField(blank=True, default=True, help_text='Se sim, o quiz não será exibido para os usuários e somente poderá ser feito por editores.', verbose_name='Rascunho')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.category', verbose_name='Categoria')),
            ],
            options={
                'verbose_name': 'Questionário',
                'verbose_name_plural': 'Questionários',
            },
        ),
        migrations.AddField(
            model_name='question',
            name='quiz',
            field=models.ManyToManyField(blank=True, to='quiz.Quiz', verbose_name='Quiz'),
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.CharField(max_length=1024, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')], verbose_name='Pontuação')),
                ('correct_answer', models.CharField(max_length=10, verbose_name='Respostas Corretas')),
                ('wrong_answer', models.CharField(max_length=10, verbose_name='Respostas Incorretas')),
                ('quiz', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.quiz', verbose_name='Questionário')),
            ],
            options={
                'verbose_name': 'Progresso do Usuário',
                'verbose_name_plural': 'Progressos dos Usuários',
            },
        ),
    ]
