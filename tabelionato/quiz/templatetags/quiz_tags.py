from django import template

register = template.Library()


@register.inclusion_tag("quiz/correct_answer.html", takes_context=True)
def correct_answer_for_all(context, question):
    answers = question.get_answer_list_with_correct()
    incorrect_list = context.get("incorrect_questions", [])
    if question.id in incorrect_list:
        user_was_incorrect = True
    else:
        user_was_incorrect = False

    return {"answers": answers, "user_was_incorrect": user_was_incorrect}


@register.filter
def answer_choice_to_string(question, answer):
    return question.answer_choice_to_string(answer)


@register.filter
def has_content(text):
    return len(str(text)) > 0


@register.filter
def check_answer(value):
    print(value[2])
    return value[2] is True
