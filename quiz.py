import random
import re
import glob
import os
import asyncio
import httpx


class BirdSound:
    def __init__(self,
                 xc_id: int,
                 url: str,
                 download_url: str,
                 recordist: str,
                 country: str,
                 location: str,
                 sound_type: str,
                 license_type: str):
        self.xc_id = f"XC{xc_id}"
        self.url = url
        self.download_url = download_url
        self.recordist = recordist
        self.country = country
        self.location = location
        self.sound_type = sound_type
        self.license_type = license_type
        self.sound_file_path = f"static/{self.xc_id}.mp3"

    async def download_sound_file(self, client):
        result = await client.get(self.download_url)
        with open(self.sound_file_path, "wb") as f:
            f.write(result.content)


class QuizSpecies:
    def __init__(self, common_name_FI: str, scientific_name: str, sounds: [], square_count: int):
        self.correct_answers = {
            "comNameFI": common_name_FI.lower().strip(),
            "sciName": scientific_name.lower().strip()
        }
        self.square_count = square_count
        self.sounds = sounds
        self.current_sound = None

    async def set_current_sound(self, client):
        successful_download = False
        while not successful_download:
            # Known bug: if download fails for all sounds for a given species, throws an index error
            random_sound_idx = random.choice(range(len(self.sounds)))
            random_sound = self.sounds[random_sound_idx]
            try:
                await random_sound.download_sound_file(client)
            except Exception as e:
                print("Download failed...")
                print(repr(e))
                self.sounds.pop(random_sound_idx)
                continue
            self.current_sound = random_sound
            print("Downloaded sound", self.current_sound.xc_id)
            successful_download = True


class Quiz:
    def __init__(self, full_species_list):
        self.full_species_list = full_species_list
        self.quiz_species_list = full_species_list
        self.current_species = None
        self.species_idx = -1
        self.score = 0
        self.answers = []

    def wildcard_filter(self, wildcard_pattern):
        if wildcard_pattern:
            regex_pattern = re.compile(rf'^{wildcard_pattern.replace("*", ".*")}$')
            matched_species_list = [sp for sp in self.quiz_species_list
                                    if regex_pattern.match(sp.correct_answers["comNameFI"])]
            if len(matched_species_list) > 0:
                self.quiz_species_list = matched_species_list

    def length_filter(self, n):
        random_species = random.sample(self.quiz_species_list, min(len(self.quiz_species_list), n))
        self.quiz_species_list = random_species

    def difficulty_filter(self, difficulty_level):
        """
        Difficulty level determines how rare the species included in the quiz are.
        The pool of possible quiz species is filtered by Atlas square count.

            Level 1 -> Top 33.3% most common species by Atlas square count are included
            Level 2 -> Top 66.6% most common
            Level 3 -> All species
            Level 4 -> Top 66.6% rarest
            Level 5 -> Top 33.3% rarest
        """
        total_species_count = len(self.quiz_species_list)
        min_square_count_ranks = {
            1: int(total_species_count / 3),
            2: int(total_species_count / 3 * 2),
            3: int(total_species_count),
            4: int(total_species_count / 3 * 2),
            5: int(total_species_count / 3),
        }
        no_of_species = min_square_count_ranks[difficulty_level]
        self.quiz_species_list = sorted(self.quiz_species_list, key=lambda x: x.square_count,
                                        reverse=difficulty_level <= 3)[:no_of_species]
        random.shuffle(self.quiz_species_list)

    def has_more_species(self):
        return self.species_idx < len(self.quiz_species_list)-1

    def next_species(self):
        self.species_idx += 1
        self.current_species = self.quiz_species_list[self.species_idx]

    async def download_all_sounds(self):
        async with httpx.AsyncClient() as client:
            tasks = [sp.set_current_sound(client) for sp in self.quiz_species_list]
            await asyncio.gather(*tasks, return_exceptions=False)

    def check_answer(self, user_answer):
        correct_answers = list(self.current_species.correct_answers.values())
        if user_answer in correct_answers:
            self.score += 1
            correct = True
        else:
            correct = False
        self.answers.append(
            {"user_answer": user_answer,
             "correct_answers": correct_answers,
             "answered_correctly": correct
             }
        )
        return correct

    def get_score(self):
        wrong = self.species_idx+1 - self.score
        score_percent = int(self.score / self.species_idx+1 * 100)
        return self.score, wrong, score_percent

    def reset(self):
        self.quiz_species_list = self.full_species_list
        self.current_species = None
        self.species_idx = -1
        self.score = 0
        self.answers = []


def delete_all_sounds():
    for f in glob.glob("static/XC*.mp3"):
        os.remove(f)
