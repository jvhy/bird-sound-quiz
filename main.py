from flask import Flask, render_template, request, redirect, session
from data_collection import reformat_recordings
from quiz import Quiz, delete_all_sounds
import secrets
import pandas as pd


df = pd.read_csv("data/recordings.csv")
species_list = reformat_recordings(df)
new_quiz = Quiz(species_list)

session_key = secrets.token_hex()
app = Flask(__name__)
app.secret_key = session_key


@app.route('/', methods=("GET", "POST"))
async def index():
    if request.method == "POST":
        difficulty = int(request.form.get("quiz-difficulty"))
        wildcard_pattern = request.form.get("wildcard")
        quiz_length = int(request.form.get("quiz-length"))
        new_quiz.difficulty_filter(difficulty)
        new_quiz.wildcard_filter(wildcard_pattern)
        new_quiz.length_filter(quiz_length)
        await new_quiz.download_all_sounds()
        new_quiz.next_species()
        session["is_initialized"] = True
        session["questions_left"] = len(new_quiz.quiz_species_list)
        session["points"] = 0
        session["max_points"] = len(new_quiz.quiz_species_list)
        session["correct"] = None
        return redirect("/quiz")
    return render_template("index.html")


@app.route('/quiz', methods=("GET", "POST"))
def quiz():
    if not session.get("is_initialized"):
        return redirect("/")
    species = new_quiz.current_species
    if request.method == "POST":
        session["questions_left"] -= 1
        answer = request.form.get("answer")
        correct = new_quiz.check_answer(answer)
        session["correct_answer"] = species.correct_answers["comNameFI"]
        if correct:
            session["points"] += 1
            session["correct"] = True
        else:
            session["correct"] = False
        if new_quiz.has_more_species():
            new_quiz.next_species()
            species = new_quiz.current_species
    return render_template("quiz_page.html", species=species)


@app.route('/results')
def results():
    if not session.get("is_initialized"):
        return redirect("/")
    elif session.get("questions_left") > 0:
        return redirect("/quiz")
    delete_all_sounds()
    new_quiz.reset()
    session["is_initialized"] = False
    session["questions_left"] = len(new_quiz.quiz_species_list)
    return render_template("results_page.html")


if __name__ == "__main__":
    app.run(debug=True)
