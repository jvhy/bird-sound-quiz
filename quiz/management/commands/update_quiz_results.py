from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.models import Quiz
from quiz.utils import check_answer


class Command(BaseCommand):
    help = "Update quiz results after answer checking logic has changed"

    def handle(self, *args, **kwargs):
        quizzes = Quiz.objects.all()
        for quiz in quizzes:
            quiz_score = 0
            answers = quiz.answers.all()
            for answer in answers:
                if answer.recording is None:  # if recording has been deleted, keep correctness as is
                    continue
                correct_species = answer.recording.species
                is_correct = check_answer(answer.user_answer, correct_species)
                quiz_score += is_correct
                answer.is_correct = is_correct
                answer.save()
            quiz.score = quiz_score
            quiz.save()

        self.stdout.write(
            self.style.SUCCESS("Successfully updated quiz results.")
        )
