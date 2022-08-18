import queries as q
import statistics
from datetime import date, datetime, timedelta
from typing import Tuple


def generate_random_facts():
    union = list(set.union(milestone_facts(), average_high_variance_facts(), date_facts(), last_session_facts(),
                           last_month_summary(), result_facts(), game_count_facts(), close_to_record(), outclassed(),
                           at_least_1_streak()))
    return sorted(union, key=lambda i: i[1], reverse=True)


# Things related to date
def date_facts() -> set[Tuple]:
    facts = set()
    # TODO: Do more special date facts
    # date_data = q.dates_table()[int(date.today().strftime('%d')) - 1]
    # month_data = q.month_table()[int(date.today().strftime('%m')) - 1]
    # year_data = q.year_table()[int(date.today().strftime('%y')) - 18]

    # facts.add((f'On the {date_data[0]} day of a month, CG wins {round(date_data[2], 1)}% of games.', 1))
    # facts.add((f'In {month_data[0]}, CG wins {round(month_data[2], 1)}% of games.', 1))
    # facts.add((f'In {year_data[0]}, CG wins {round(year_data[2], 1)}% of games.', 1))
    return facts


# Last session was xy
def last_session_facts() -> set[Tuple]:
    facts = set()
    session_id, session_date, wins, losses, goals, against, knus_score, knus_goals, knus_assists, knus_saves, knus_shots, puad_score, puad_goals, puad_assists, puad_saves, puad_shots, sticker_score, sticker_goals, sticker_assists, sticker_saves, sticker_shots, quality = q.last_session_data()
    if session_id % 50 == 0:
        facts.add((f'Last session was special, it was the {session_id}th session! 😂', 4))

    # First session in x days, first session in a month, first session in a year, at the same date x years ago TODO:
    #  cleanup
    d1, d2 = q.last_two_sessions_dates()
    diff = (datetime.today() - datetime.strptime(d2[0], "%Y-%m-%d")).days
    if d1[0] == datetime.today().date():
        facts.add((f'The last session before today was {diff} days ago... 🤡', 2))
    else:
        if diff <= 7:
            facts.add((f'The last session was {diff} days ago.', 2))
        elif diff <= 14:
            facts.add((f'Last session was {diff} days ago...', 3))
        elif diff <= 21:
            facts.add((f'Last session is already {diff} days ago 🤡🤡🤡', 4))

    # TODO: Do more with unused stats
    return facts


def game_count_facts() -> set[Tuple]:
    facts = set()
    month, year, total = q.game_amount_this_month(), q.game_amount_this_year(), q.max_id()
    if total % 100 == 0:
        facts.add((f'You just played the {total}th game in total.', 4))

    if year % 50 == 0:
        facts.add((f'You just played the {year}th game this year.', 4))

    if month % 25 == 0:
        facts.add((f'You just played the {month}th game this month.', 3))
    return facts


def last_month_summary() -> set[Tuple]:
    facts = set()
    games_this_month = q.game_amount_this_month()

    # Only show if less than 3 games have been played this month and its before the fifth of a month
    if games_this_month <= 5 and datetime.today().day < 5:
        last_month_str = (datetime.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        data = q.unique_months_game_count()

        # Cursed, fix it sometime
        c = 0
        count = None
        for tp in data:
            c = c + 1
            if tp[0] == last_month_str:
                count = tp[1]

        facts.add((f'Last month, you played {count} games, which ranks at {c}. among all months.', 5))
    return facts


# Unusual result
def result_facts() -> set[Tuple]:
    facts = set()
    data = q.results_table()
    goals, against = q.last_result()
    for entry in data:
        if entry[0] == goals and entry[1] == against:
            total, percent = entry[2], entry[3]
            if percent >= 0.05:
                facts.add(
                    (
                        f'The result of the last match was extremely common. It already happened {total} times. ('
                        f'{round(percent * 100, 1)}%)',
                        1))
            elif percent >= 0.025:
                facts.add(
                    (
                        f'The result of the last match was common. In total, it happened {total} times. ('
                        f'{round(percent * 100, 2)}%)',
                        2))
            elif percent >= 0.0125:
                facts.add(
                    (
                        f'The result of last match was rare, in total it happened {total} times ('
                        f'{round(percent * 100, 4)}%)',
                        3))
            elif percent >= 0.00625:
                facts.add(
                    (
                        f'The result of last match was really rare, in total it happened {total} times ('
                        f'{round(percent * 100, 4)}%)',
                        4))
            else:
                facts.add(
                    (
                        f"The result of last match only happened for the {total}. time! That's only "
                        f"{round(percent * 100, 4)}%",
                        5))
    if not facts:  # set is empty because results has not happened before
        facts.add(
            (f'Last game was the first time that this result happened. {goals}:{against}, a real rarity.', 5))
    return facts


# Player reaches milestone in stat y
def milestone_facts() -> set[Tuple]:
    facts = set()
    possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']

    for stat in possible_stats:
        for p in range(0, 3):
            milestone_val = 50000 if stat == 'score' else 500 if stat == 'shots' else 250
            total = q.player_total_of_stat(p, stat)
            overshoot = total % milestone_val
            if overshoot < q.player_stat_of_last_game(p, stat):  # Milestone crossed
                facts.add((f'{q.p_name(p)} just reached {total - overshoot} {stat}!', 4))
    return facts


# Player average is higher/lower in last x games than total avg
def average_high_variance_facts() -> set[Tuple]:
    facts = set()
    possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']
    z_values = {'Top 1%': 2.32635, 'Top 5%': 1.64485, 'Top 15%': 1.03643,
                'Bottom 1%': -2.32635, 'Bottom 5%': -1.64485, 'Bottom 15%': -1.03643}

    for stat in possible_stats:
        for p in range(0, 3):
            for s in [(20, q.performance(p, stat)), (100, q.performance100(p, stat)), (250, q.performance250(p, stat))]:
                for z in z_values.keys():
                    percentile_value = q.player_average_all_games(p, stat) + z_values[z] * statistics.stdev(
                        q.average_all(p, stat))
                    if percentile_value < s[1] and z.startswith('Top'):
                        facts.add((f'Over the last {s[0]} games, {q.p_name(p)} {stat} are in the {z} on average.', 3))
                        break
                    elif percentile_value > s[1] and z.startswith('Bottom'):
                        facts.add(
                            (f'Over the last {s[0]} games, {q.p_name(p)} {stat} are only in the {z} on average.', 3))
                        break

    return facts


# Came close to a record
def close_to_record() -> set[Tuple]:  # TODO: make it faster
    facts = set()

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
    # Iterate through data and check if last gameID appears
    for record in record_data:
        for index in range(0, limit):
            if record[0][index][2] == last_id:
                facts.add((record[1].format(value=record[0][index][1], name=record[0][index][0], rank=index + 1), 4))

    # TODO: Session is close to being a record session
    session_count = q.session_count()
    record_data = q.record_stat_per_session('games', limit)
    return facts


# X has double the amount of Y, also session/season based
def outclassed() -> set[Tuple]:
    return set()


# 'At least 1' streak in Goals/Assists/Saves
def at_least_1_streak() -> set[Tuple]:
    return set()


if __name__ == '__main__':
    print(generate_random_facts())
