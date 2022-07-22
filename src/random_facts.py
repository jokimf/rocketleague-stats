import queries as q
import statistics
from datetime import date


def generate_fun_facts() -> set[str]:
    return set.union(milestone(), average_high_variance(), date_things())


# Things related to date
def date_things() -> set[str]:
    facts = set()

    date_data = q.dates()[int(date.today().strftime('%d')) - 1]
    month_data = q.months()[int(date.today().strftime('%m')) - 1]
    year_data = q.years()[int(date.today().strftime('%y')) - 18]

    facts.add(f'On the {date_data[0]} day of a month, CG wins {round(date_data[2], 1)}% of games.')
    facts.add(f'In {month_data[0]}, CG wins {round(month_data[2], 1)}% of games.')
    facts.add(f'In {year_data[0]}, CG wins {round(year_data[2], 1)}% of games.')
    return facts


# Last session was xy TODO: needs SQL session view
def last_session_info() -> set[str]:
    pass


# Unusual result
def unusual_result() -> set[str]:
    pass


# Came close to a record
def close_to_record() -> set[str]:
    pass


# X has double the amount of Y, also session/season based
def outclassed() -> set[str]:
    pass


# 'At least 1' streak in Goals/Assists/Saves
def at_least_1_streak() -> set[str]:
    pass


# Player average is higher/lower in last x games than total avg
def average_high_variance() -> set[str]:
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


# Player reaches milestone in stat y
def milestone() -> set[str]:
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


print(generate_fun_facts())
