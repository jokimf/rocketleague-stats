import queries as q
import statistics
from datetime import date, datetime, timedelta


def generate_fun_facts() -> set[str]:
    return set.union(milestone_facts(), average_high_variance_facts(), date_facts(), last_session_facts(),
                     last_month_summary(), result_facts(), game_count_facts(), close_to_record(), outclassed(),
                     at_least_1_streak())


# Things related to date
def date_facts() -> set[str]:
    facts = set()

    date_data = q.dates_table()[int(date.today().strftime('%d')) - 1]
    month_data = q.month_table()[int(date.today().strftime('%m')) - 1]
    year_data = q.year_table()[int(date.today().strftime('%y')) - 18]

    facts.add(f'On the {date_data[0]} day of a month, CG wins {round(date_data[2], 1)}% of games.')
    facts.add(f'In {month_data[0]}, CG wins {round(month_data[2], 1)}% of games.')
    facts.add(f'In {year_data[0]}, CG wins {round(year_data[2], 1)}% of games.')
    return facts


# Last session was xy
def last_session_facts() -> set[str]:
    facts = set()
    session_id, session_date, wins, losses, goals, against, knus_score, knus_goals, knus_assists, knus_saves, knus_shots, \
    puad_score, puad_goals, puad_assists, puad_saves, puad_shots, sticker_score, sticker_goals, sticker_assists, \
    sticker_saves, sticker_shots, quality = q.last_session_data()
    if session_id % 50 == 0:
        facts.add(f'Last session was special, it was the {session_id}th session! 😂')

    # First session in x days, first session in a month, first session in a year, at the same date x years ago
    d1, d2 = q.last_two_sessions_dates()
    diff = (datetime.strptime(d1[0], "%Y-%m-%d") - datetime.strptime(d2[0], "%Y-%m-%d")).days
    if d1[0] == datetime.today().date():
        facts.add(f'The last session before today was {diff} days ago... 🤡')
    else:
        if diff <= 7:
            facts.add(f'The last session was {diff} days ago.')
        elif diff <= 14:
            facts.add(f'Last session was {diff} days ago...')
        elif diff <= 21:
            facts.add(f'Last session is already {diff} days ago 🤡🤡🤡')

    # TODO: Do more with unused stats
    return facts


def game_count_facts() -> set[str]:
    facts = set()
    month, year, total = q.games_this_month(), q.games_this_year(), q.max_id()
    if total % 100 == 0:
        facts.add(f'You just played the {total}th game in total.')

    if year % 50 == 0:
        facts.add(f'You just played the {year}th game this year.')

    if month % 25 == 0:
        facts.add(f'You just played the {month}th game this month.')

    return facts


def last_month_summary() -> set[str]:
    facts = set()
    month = q.games_this_month()

    # Only show if less than 3 games have been played this month and its before the fifth of a month
    if month <= 3 and datetime.today().day < 5:
        last_month_str = (datetime.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        data = q.month_game_counts()

        # Cursed, fix it sometime
        c = 0
        count = None
        for tp in data:
            c = c + 1
            if tp[0] == last_month_str:
                count = tp[1]

        facts.add(f'Last month, you played {count} games, which ranks at {c}. among all months.')
    return facts


# Unusual result
def result_facts() -> set[str]:
    facts = set()
    data = q.results_table()
    goals, against = q.last_result()
    for entry in data:
        if entry[0] == goals and entry[1] == against:
            total, percent = entry[2], entry[3]
            if percent >= 0.05:
                facts.add(
                    f'The result of the last match was extremely common. It already happened {total} times. ({round(percent * 100, 1)}%)')
            elif percent >= 0.025:
                facts.add(
                    f'The result of the last match was common. In total, it happened {total} times. ({round(percent * 100, 2)}%)')
            elif percent >= 0.0125:
                facts.add(
                    f'The result of last match was rare, in total it happened {total} times ({round(percent * 100, 4)}%)')
            elif percent >= 0.00625:
                facts.add(
                    f'The result of last match was really rare, in total it happened {total} times ({round(percent * 100, 4)}%)')
            else:
                facts.add(
                    f"The result of last match only happened for the {total}. time! That's only {round(percent * 100, 4)}%")
    if not facts:  # set is empty because results has not happened before
        facts.add(
            f'Last game was the first time that this result happened. {goals}:{against}, a real rarity.')
    return facts


# Player reaches milestone in stat y
def milestone_facts() -> set[str]:
    facts: set[str] = set()
    possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']

    for stat in possible_stats:
        for p in range(0, 3):
            milestone_val = 50000 if stat == 'score' else 500 if stat == 'shots' else 250
            total = q.total(p, stat)
            overshoot = total % milestone_val
            if overshoot < q.last(p, stat):  # Milestone crossed
                facts.add(f'{q.player_name(p)} just reached {total - overshoot} {stat}!')
    return facts


# Player average is higher/lower in last x games than total avg
def average_high_variance_facts() -> set[str]:
    facts: set[str] = set()
    possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']
    z_values = {"Top 1%": 2.32635, "Top 5%": 1.64485, 'Top 15%': 1.03643,
                'Bottom 15%': -1.03643, 'Bottom 5%': -1.64485, 'Bottom 1%': -2.32635}

    for stat in possible_stats:
        for p in range(0, 3):
            for s in [(20, q.performance(p, stat)), (100, q.performance100(p, stat)), (250, q.performance250(p, stat))]:
                for z in z_values.keys():
                    percentile_value = q.average(p, stat) + z_values[z] * statistics.stdev(q.average_all(p, stat))
                    if percentile_value < s[1] and z.startswith('Top'):
                        facts.add(f'Over the last {s[0]} games, {q.player_name(p)} {stat} are in the {z} on average.')
                    elif percentile_value > s[1] and z.startswith('Bottom'):
                        facts.add(
                            f'Over the last {s[0]} games, {q.player_name(p)} {stat} are only in the {z} on average.')

    return facts


# Came close to a record
def close_to_record() -> set[str]:
    facts = set()

    # TODO: Session is close to being a record session

    # Record games
    last_id = q.max_id()
    one_percent_threshold = round(last_id / 100)
    highest_score = q.record_highest_value_per_stat('score', one_percent_threshold)
    highest_goals = q.record_highest_value_per_stat('goals', one_percent_threshold)
    highest_assists = q.record_highest_value_per_stat('assists', one_percent_threshold)
    highest_saves = q.record_highest_value_per_stat('saves', one_percent_threshold)
    highest_shots = q.record_highest_value_per_stat('shots', one_percent_threshold)
    most_without_goal = q.most_points_without_goal(one_percent_threshold)
    least_with_goal = q.least_points_with_goals(one_percent_threshold)
    most_against = q.most_against(one_percent_threshold)
    most_against_and_won = q.most_against_and_won(one_percent_threshold)
    most_goals_and_lost = q.most_goals_and_lost(one_percent_threshold)
    most_total_goals = q.most_total_goals(one_percent_threshold)
    highest_team_score = q.highest_team('score', one_percent_threshold)
    highest_team_goals = q.highest_team('goals', one_percent_threshold)
    highest_team_assists = q.highest_team('assists', one_percent_threshold)
    highest_team_saves = q.highest_team('saves', one_percent_threshold)
    highest_team_shots = q.highest_team('shots', one_percent_threshold)

    # TODO: put into function
    for i in range(0, one_percent_threshold):
        if highest_score[i][2] == last_id:
            facts.add(
                f'The score of {highest_score[i][1]} reached by {highest_score[i][0]} last game was in the Top 1% of all scores, ranking at spot number {i}!')
        if highest_goals[i][2] == last_id:
            facts.add(
                f'The goal amount of {highest_goals[i][1]} reached by {highest_goals[i][0]} last game was in the Top 1% of all games, ranking at spot number {i}!')
        if highest_assists[i][2] == last_id:
            facts.add(
                f'The assist amount of {highest_assists[i][1]} reached by {highest_assists[i][0]} last game was in the Top 1% of all games, ranking at spot number {i}!')
        if highest_saves[i][2] == last_id:
            facts.add(
                f'The save amount of {highest_saves[i][1]} reached by {highest_saves[i][0]} last game was in the Top 1% of all games, ranking at spot number {i}!')
        if highest_shots[i][2] == last_id:
            facts.add(
                f'The shot amount of {highest_shots[i][1]} reached by {highest_shots[i][0]} last game was in the Top 1% of all games, ranking at spot number {i}!')
        if most_without_goal[i][2] == last_id:
            facts.add(
                f'A total amount of {most_without_goal[i][1]} was reached by {most_without_goal[i][0]} last game, without scoring! It was in the Top 1% of score without a goal, ranking at spot number {i}!')
        if least_with_goal[i][2] == last_id:
            facts.add(
                f'{least_with_goal[i][0]} only reached a total amount of {least_with_goal[i][1]} score, even though he scored... he was in the Bottom 1% of score having scored at least one goal, ranking at spot number {i}!')
        if most_against[i][2] == last_id:
            facts.add(
                f'Last game you conceded a top 1% amount of goals... {most_against[i][1]} in total. It ranks at number {i} of all games')
        if most_against_and_won[i][2] == last_id:
            facts.add(
                f'Last game you conceded a total of {most_against_and_won[i][1]} goals - but still won. The game ranks at number {i} in that regard.')
        if most_goals_and_lost[i][2] == last_id:
            facts.add(
                f'Last game you scored a total of {most_goals_and_lost[i][1]} goals, but still lost. The game ranks at number {i} in that regard.')
        if most_total_goals[i][2] == last_id:
            facts.add(
                f'Last game you scored a total of {most_total_goals[i][1]} goals. The game ranks at number {i} in that regard.')
    # TODO: Player gets close to performance best/worst
    # TODO: Player or team gets close to record in absolute value
    data = q.record_stat_per_session('games', one_percent_threshold)
    return facts


close_to_record()


# X has double the amount of Y, also session/season based
def outclassed() -> set[str]:
    return set()


# 'At least 1' streak in Goals/Assists/Saves
def at_least_1_streak() -> set[str]:
    return set()


print(generate_fun_facts())
