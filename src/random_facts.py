import math

import queries as q
import statistics
from datetime import date, datetime, timedelta
from typing import Tuple, List

import time
import timeit


def timer_func(func):
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        runtime = time.time() - start
        print(f"{func.__name__} took {runtime} seconds to complete its execution.")
        return value

    return function_timer


def generate_random_facts():
    union = record_session() + milestone_facts() + date_facts() + last_session_facts() + last_month_summary() + result_facts() + game_count_facts() + close_to_record() + outclassed() + at_least_1_streak()
    return sorted(union, key=lambda i: i[1], reverse=True)


# Things related to date
@timer_func
def date_facts() -> List[Tuple]:
    facts = []
    # TODO: Do more special date facts
    # date_data = q.dates_table()[int(date.today().strftime('%d')) - 1]
    # month_data = q.month_table()[int(date.today().strftime('%m')) - 1]
    # year_data = q.year_table()[int(date.today().strftime('%y')) - 18]

    # facts.append((f'On the {date_data[0]} day of a month, CG wins {round(date_data[2], 1)}% of games.', 1))
    # facts.append((f'In {month_data[0]}, CG wins {round(month_data[2], 1)}% of games.', 1))
    # facts.append((f'In {year_data[0]}, CG wins {round(year_data[2], 1)}% of games.', 1))
    return facts


# Last session was xy
@timer_func
def last_session_facts() -> List[Tuple]:
    facts = []
    session_id, session_date, wins, losses, goals, against, knus_score, knus_goals, knus_assists, knus_saves, knus_shots, puad_score, puad_goals, puad_assists, puad_saves, puad_shots, sticker_score, sticker_goals, sticker_assists, sticker_saves, sticker_shots, quality = q.last_session_data()
    if session_id % 50 == 0:
        facts.append((f'This session is special, it was the {session_id}th session! 😂', 4))

    # First session in x days, first session in a month, first session in a year, at the same date x years ago TODO:
    #  cleanup
    d1, d2 = q.last_two_sessions_dates()
    diff = (datetime.today() - datetime.strptime(d2[0], "%Y-%m-%d")).days
    if d1[0] == datetime.today().date():
        facts.append((f'The last session before today was {diff} days ago... 🤡', 2))
    else:
        if 7 >= diff >= 5:
            facts.append((f'The last session was {diff} days ago.', 2))
        elif diff <= 14:
            facts.append((f'Last session was {diff} days ago...', 3))
        elif diff <= 21:
            facts.append((f'Last session is already {diff} days ago 🤡🤡🤡', 4))

    # TODO: Do more with unused stats
    return facts


@timer_func
def game_count_facts() -> List[Tuple]:
    facts = []
    month, year, total = q.game_amount_this_month(), q.game_amount_this_year(), q.max_id()
    if total % 100 == 0:
        facts.append((f'You just played the {total}th game in total.', 4))

    if year % 50 == 0:
        facts.append((f'You just played the {year}th game this year.', 4))

    if month % 25 == 0:
        facts.append((f'You just played the {month}th game this month.', 3))
    return facts


@timer_func
def last_month_summary() -> List[Tuple]:
    facts = []
    games_this_month = q.game_amount_this_month()

    # Only show if less than 3 games have been played this month and its before the fifth of a month
    if 5 >= games_this_month > 0 and datetime.today().day < 5:
        last_month_str = (datetime.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        data = q.unique_months_game_count()

        # Cursed, fix it sometime
        c = 0
        count = None
        for tp in data:
            c = c + 1
            if tp[0] == last_month_str:
                count = tp[1]

        facts.append((f'Last month, you played {count} games, which ranks at {c}. among all months.', 5))
    return facts


# Unusual result
@timer_func
def result_facts() -> List[Tuple]:
    facts = []
    data = q.results_table()
    goals, against = q.last_result()
    for entry in data:
        if entry[0] == goals and entry[1] == against:
            total, percent = entry[2], entry[3]
            if percent >= 0.05:
                facts.append(
                    (
                        f'The result of the last match was extremely common. It already happened {total} times. ('
                        f'{round(percent * 100, 1)}%)',
                        1))
            elif percent >= 0.025:
                facts.append(
                    (
                        f'The result of the last match was common. In total, it happened {total} times. ('
                        f'{round(percent * 100, 2)}%)',
                        2))
            elif percent >= 0.0125:
                facts.append(
                    (
                        f'The result of last match was rare, in total it happened {total} times ('
                        f'{round(percent * 100, 4)}%)',
                        3))
            elif percent >= 0.00625:
                facts.append(
                    (
                        f'The result of last match was really rare, in total it happened {total} times ('
                        f'{round(percent * 100, 4)}%)',
                        4))
            else:
                facts.append(
                    (
                        f"The result of last match only happened for the {total}. time! That's only "
                        f"{round(percent * 100, 4)}%",
                        5))
    if not facts:  # set is empty because results has not happened before
        facts.append(
            (f'Last game was the first time that this result happened. {goals}:{against}, a real rarity.', 5))
    return facts


# Player reaches milestone in stat y
@timer_func
def milestone_facts() -> List[Tuple]:
    facts = []
    possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']

    for stat in possible_stats:
        for p in range(0, 3):
            milestone_val = 50000 if stat == 'score' else 500 if stat == 'shots' else 250
            total = q.player_total_of_stat(p, stat)
            overshoot = total % milestone_val
            if overshoot < q.player_stat_of_last_game(p, stat):  # Milestone crossed
                facts.append((f'{q.player_name(p)} just reached {total - overshoot} {stat}!', 4))
    return facts


# Came close to a record
@timer_func
def close_to_record() -> List[Tuple]:  # TODO: make it faster
    facts = []

    # Record games
    last_id = q.max_id()
    limit = 100  # round(last_id / 100) # TODO: find better metric, some crash for max_id
    record_data = [(q.record_highest_value_per_stat('score', limit),
                    'The score of {value} reached by {name} last game was in the Top 100 of all scores, ranking at '
                    'spot number {rank}!'),
                   (q.record_highest_value_per_stat('goals', limit),
                    'The goal amount of {value} reached by {name} last game was in the Top 100 of all games, '
                    'ranking at spot number {rank}!'),
                   (q.record_highest_value_per_stat('assists', limit),
                    'The assist amount of {value} reached by {name} last game was in the Top 100 of all games, '
                    'ranking at spot number {rank}!'),
                   (q.record_highest_value_per_stat('saves', limit),
                    'The save amount of {value} reached by {name} last game was in the Top 100 of all games, '
                    'ranking at spot number {rank}!'),
                   (q.record_highest_value_per_stat('shots', limit),
                    'The shot amount of {value} reached by {name} last game was in the Top 100 of all games, '
                    'ranking at spot number {rank}!'),
                   (q.most_points_without_goal(limit),
                    '''A total amount of {value} points was reached by {name} last game, without scoring! 
                       It was in the Top 100 of score without a goal, ranking at spot number {rank}!'''),
                   (q.least_points_with_goals(limit),
                    '{name} only reached a total amount of {value} score, even though he scored... he was in the '
                    'Bottom 100 of score having scored at least one goal, ranking at spot number {rank}!'),
                   (q.most_against(limit),
                    'Last game you conceded a Top 100 amount of goals... {value} in total. It ranks at number {rank} '
                    'of all games'),
                   (q.most_against_and_won(limit),
                    'Last game you conceded a total of {value} goals, but still won. The game ranks at number {rank} '
                    'in that regard.'),
                   (q.most_goals_and_lost(limit),
                    'Last game you scored a total of {value} goals, but still lost. The game ranks at number {rank} '
                    'in that regard.'),
                   (q.most_total_goals(limit),
                    'Last game, both teams scored a total of {value} goals. The game ranks at number {rank} in that '
                    'regard.'),
                   (q.highest_team('score', limit),
                    'Last game you scored a total of {value} points. The game ranks at number {rank} in that regard.'),
                   (q.highest_team('goals', limit),
                    'Last game you scored a total of {value} goals. The game ranks at number {rank} in that regard.'),
                   (q.highest_team('assists', limit),
                    'Last game you got a total of {value} assists. The game ranks at number {rank} in that regard.'),
                   (q.highest_team('saves', limit),
                    'Last game you scored a total of {value} goals. The game ranks at number {rank} in that regard.'),
                   (q.highest_team('shots', limit),
                    'Last game you scored a total of {value} goals. The game ranks at number {rank} in that regard.'),
                   (q.diff_mvp_lvp('DESC', limit),
                    'Last game the difference between the MVP and LVP was {value} points. That is the {rank}. highest '
                    'difference.'),
                   (q.diff_mvp_lvp('ASC', limit),
                    'Last game the difference between the MVP and LVP was only {value} points. That is the {rank}. '
                    'lowest difference.'),
                   (q.most_solo_goals(limit),
                    'Last game had with {value} goals an usual amount of solo goals. The game ranks at number {rank} '
                    'in that regard.'),
                   (q.trend('score', 'MIN', limit),
                    'The point trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                    'total.'),
                   (q.trend('score', 'MAX', limit),
                    'The point trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                    'total.'),
                   (q.trend('goals', 'MIN', limit),
                    'The goal trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.'),
                   (q.trend('goals', 'MAX', limit),
                    'The goal trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                    'total.'),
                   (q.trend('assists', 'MIN', limit),
                    'The assist trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                    'total.'),
                   (q.trend('assists', 'MAX', limit),
                    'The assist trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                    'total.'),
                   (q.trend('saves', 'MIN', limit),
                    'The saves trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                    'total.'),
                   (q.trend('saves', 'MAX', limit),
                    'The saves trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                    'total.'),
                   (q.trend('shots', 'MIN', limit),
                    'The shots trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                    'total.'),
                   (q.trend('shots', 'MAX', limit),
                    'The shots trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                    'total.')
                   ]
    # Iterate through data and check if last gameID appears # TODO Check only threshold
    for record in record_data:
        for index in range(0, limit):
            if record[0][index][2] == last_id:
                facts.append((record[1].format(value=record[0][index][1], name=record[0][index][0], rank=index + 1), 4))

    return facts


@timer_func
def record_session() -> List[Tuple]:
    facts = []
    # TODO: Session is close to being a record session
    session_count = q.session_count()
    session_limit = math.ceil(session_count)  # top 2%

    session_record_data = q.record_games_per_session(session_limit)
    next_milestone_rank = None
    next_milestone_value = None
    for rank in range(0, session_limit):
        if (rank + 1) % 5 == 0 and session_record_data[rank][0] != session_count:
            next_milestone_rank = rank + 1
            next_milestone_value = session_record_data[rank][1]
        if session_record_data[rank][0] == session_count and session_record_data[rank][1] > 10:
            facts.append((
                f'You played {session_record_data[rank][1]} games this session. It ranks at spot number {rank + 1} in that regard.',
                4))
            if next_milestone_value is not None and next_milestone_rank is not None:
                games_to_reach_milestone = next_milestone_value - session_record_data[rank][1]
                facts.append((
                    f'To reach rank {next_milestone_rank} in games played this session, you need to play {1 if games_to_reach_milestone == 0 else games_to_reach_milestone} more games.',
                    4))
    return facts


# X has double the amount of Y, also session/season based
def outclassed() -> List[Tuple]:
    facts = []
    return facts


# 'At least 1' streak in Goals/Assists/Saves
def at_least_1_streak() -> List[Tuple]:
    facts = []
    return facts


# Streak of stats
def streak() -> List[Tuple]:
    facts = []
    return facts


if __name__ == '__main__':
    print(generate_random_facts())
