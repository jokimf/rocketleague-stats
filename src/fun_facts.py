import queries as q
import statistics


def generate_fun_facts() -> set[str]:
    return set.union(milestone(), average_high_variance())


# Things related to date
def date_things() -> set[str]:
    pass


# Last session was xy
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
