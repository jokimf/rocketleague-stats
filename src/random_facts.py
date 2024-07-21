import math
from datetime import datetime, timedelta
from typing import Any

from dateutil.relativedelta import relativedelta

from connect import BackendConnection
from queries import RLQueries
from records import RecordQueries

random_facts = list()
class RandomFactQueries(BackendConnection):
    def __init__(self) -> None:
        super().__init__()
        self.q = RLQueries()
        self.r = RecordQueries()
        global random_facts
        random_facts = self.generate_random_facts() # First time it is loaded, generate random facts


    # Invoked every time data is added
    def generate_random_facts(self) -> list:
        union = self.record_session() + self.milestone_facts() + self.date_facts() + self.last_session_facts() + self.last_month_summary() + \
                self.result_facts() + self.game_count_facts() + self.close_to_record() + self.outclassed() + self.at_least_1_streak() + self.streak()
        return sorted(union, key=lambda i: i[1], reverse=True)


    # Things related to date
    def date_facts(self) -> list[tuple]:
        facts = []
        # TODO: Do more special date facts
        # date_data = q.dates_table()[int(date.today().strftime('%d')) - 1]
        # month_data = q.month_table()[int(date.today().strftime('%m')) - 1]
        # year_data = q.year_table()[int(date.today().strftime('%y')) - 18]

        # facts.append((f'On the {date_data[0]} day of a month, CG wins {round(date_data[2], 1)}% of games.', 1))
        # facts.append((f'In {month_data[0]}, CG wins {round(month_data[2], 1)}% of games.', 1))
        # facts.append((f'In {year_data[0]}, CG wins {round(year_data[2], 1)}% of games.', 1))
        return facts

    def session_data_by_date(self, date: str):
        self.c.execute("SELECT * FROM sessions WHERE date=%s", (date,))
        return self.c.fetchone()

    # Last session was xy
    def last_session_facts(self) -> list[tuple]:
        def last_two_sessions_dates() -> list[Any]:
            self.c.execute('SELECT date FROM sessions ORDER BY SessionID DESC LIMIT 2')
            return self.c.fetchall()
        facts = []
        session_id, session_date, wins, losses, goals, against, quality = self.q.latest_session_main_data()

        # Session ID milestone
        if session_id % 50 == 0:
            facts.append((f'This session is the {session_id}th session!', 4))

        today: datetime.datetime = datetime.today()
        # Last session was x days ago
        diff = (today - datetime.strptime(last_two_sessions_dates()[0][0], "%Y-%m-%d")).days
        if diff >= 21:
            facts.append((f'The last session was as far back as {diff} days ago!', 4))
        elif diff >= 12:
            facts.append((f'The last session was {diff} days ago...', 3))
        elif diff >= 5:
            facts.append((f'The last session was {diff} days ago.', 2))

        # At the same date x years ago
        for years_ago in range(1, today.year - 2018):
            same_date = self.session_data_by_date((today - relativedelta(years=years_ago)).strftime("%Y-%m-%d"))
            if same_date:
                facts.append((
                    f'''On this day, {years_ago} years ago, you played a session 
                    with {same_date[2]} wins and {same_date[3]} losses!''',
                    3))
        return facts


    def game_count_facts(self) -> list[tuple]:
        def game_amount_this_year() -> int:
            self.c.execute("SELECT COUNT(*) FROM games WHERE YEAR(date) = YEAR(CURDATE())")
            return self.c.fetchone()[0]

        facts = []
        month, year, total = self.game_amount_this_month(), game_amount_this_year(), self.q.total_games()
        if total % 100 == 0 and total > 0:
            facts.append((f'You just played the {total}th game in total.', 4))

        if year % 50 == 0 and year > 0:
            facts.append((f'You just played the {year}th game this year.', 4))

        if month % 25 == 0 and month > 0:
            facts.append((f'You just played the {month}th game this month.', 3))
        return facts


    def last_month_summary(self) -> list[tuple]:
        def unique_months_game_count() -> list[Any]:
            self.c.execute("SELECT strftime('%m-%Y',date) as d, COUNT(*) c FROM games GROUP BY d ORDER BY c DESC")
            return self.c.fetchall()

        facts = []
        games_this_month: int = self.game_amount_this_month()

        # Only show if less than 3 games have been played this month, and it's before the fifth of a month
        if 5 >= games_this_month > 0 and datetime.today().day < 5:
            last_month_str = (datetime.today().replace(day=1) - timedelta(days=1)).strftime("%m-%Y")
            month_gc = unique_months_game_count()

            # Works because month are sorted by game count
            rank = [months[0] for months in month_gc].index(last_month_str)
            game_amount = [t for t in month_gc if t[0] == last_month_str][0][1]
            facts.append((f'Last month, you played {game_amount} games, which ranks at {rank} out of {len(month_gc)}.', 5))
        return facts


    # Unusual result
    def result_facts(self) -> list[tuple]:
        def results_table() -> list[Any]:
            self.c.execute("""
                SELECT goals, against, COUNT(g.gameID) AS c FROM games g
                GROUP BY goals, against ORDER BY 1, 2
            """)
            return self.c.fetchall()
        
        def last_result() -> tuple:
            self.c.execute('SELECT goals, against FROM games ORDER BY gameID DESC LIMIT 1')
            return self.c.fetchone()

        facts = []
        results = results_table()
        goals, against = last_result()
        for single_result in results:
            if single_result[0] == goals and single_result[1] == against:
                total, percent = single_result[2], single_result[2] / self.q.total_games()
                if percent <= 0.0025:
                    facts.append((f"The result of last match only happened for the {total}. time! That's only "
                            f"{round(percent * 100, 4)}%", 5))
                elif percent <= 0.01:
                    facts.append((
                            f'The result of last match was really rare, in total it happened {total} times ('
                            f'{round(percent * 100, 4)}%)', 4))
                elif percent <= 0.04:
                    facts.append((
                        f'The result of last match was rare, in total it happened {total} times ({round(percent * 100, 4)}%)', 3))
                elif percent < 0.0025:
                    facts.append((f'Last game was the first time that this result happened. {goals}:{against}, a real rarity.', 5))
        return facts


    # Player reaches milestone in stat y
    def milestone_facts(self) -> list[tuple]:

        def player_total_of_stat(player_id: int, stat: str) -> int:
            if stat not in possible_stats:
                raise ValueError(f'{stat} is not in possible stats.')
            self.c.execute(f'SELECT SUM({stat}) FROM scores WHERE playerID = %s', (player_id,))
            return self.c.fetchone()[0]
        
        def player_stat_of_last_game(player_id: int, stat: str) -> int:
            if stat not in possible_stats:
                raise ValueError(f'{stat} is not in possible stats.')
            self.c.execute(f'SELECT {stat} FROM scores WHERE playerID = %s ORDER BY gameID DESC LIMIT 1', (player_id,))
            return self.c.fetchone()[0]

        facts = []
        possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']

        for stat in possible_stats:
            for player_id in range(3):
                milestone_val = 50000 if stat == 'score' else 500 if stat == 'shots' else 250
                total = player_total_of_stat(player_id, stat)
                overshoot = total % milestone_val
                if overshoot < player_stat_of_last_game(player_id, stat):  # Milestone crossed
                    facts.append((f'{self.player_name(player_id)} just reached {total - overshoot} {stat}!', 4))
        return facts

    # Came close to a record
    def close_to_record(self) -> list[tuple]:
        facts = []

        # Record games
        last_id = self.q.total_games()
        limit = 100  # round(last_id / 100) # TODO: find better metric, some crash for total_games
        record_data = [(self.r.record_highest_value_per_stat('score', limit),
                        'The score of {value} reached by {name} last game was in the Top 100 of all scores, ranking at '
                        'spot number {rank}!'),
                    (self.r.record_highest_value_per_stat('goals', limit),
                        'The goal amount of {value} reached by {name} last game was in the Top 100 of all games, '
                        'ranking at spot number {rank}!'),
                    (self.r.record_highest_value_per_stat('assists', limit),
                        'The assist amount of {value} reached by {name} last game was in the Top 100 of all games, '
                        'ranking at spot number {rank}!'),
                    (self.r.record_highest_value_per_stat('saves', limit),
                        'The save amount of {value} reached by {name} last game was in the Top 100 of all games, '
                        'ranking at spot number {rank}!'),
                    (self.r.record_highest_value_per_stat('shots', limit),
                        'The shot amount of {value} reached by {name} last game was in the Top 100 of all games, '
                        'ranking at spot number {rank}!'),
                    (self.r.most_points_without_goal(limit),
                        '''A total amount of {value} points was reached by {name} last game, without scoring! 
                        It was in the Top 100 of score without a goal, ranking at spot number {rank}!'''),
                    (self.r.least_points_with_goals(limit),
                        '{name} only reached a total amount of {value} score, even though he scored... he was in the '
                        'Bottom 100 of score having scored at least one goal, ranking at spot number {rank}!'),
                    (self.r.most_against(limit),
                        'Last game you conceded a Top 100 amount of goals... {value} in total. It ranks at number {rank} '
                        'of all games'),
                    (self.r.most_against_and_won(limit),
                        'Last game you conceded a total of {value} goals, but still won. The game ranks at number {rank} '
                        'in that regard.'),
                    (self.r.most_goals_and_lost(limit),
                        'Last game you scored a total of {value} goals, but still lost. The game ranks at number {rank} '
                        'in that regard.'),
                    (self.r.most_total_goals(limit),
                        'Last game, both teams scored a total of {value} goals. The game ranks at number {rank} in that '
                        'regard.'),
                    (self.r.highest_stat_sum_team('score', limit),
                        'Last game you scored a total of {value} points. The game ranks at number {rank} in that regard.'),
                    (self.r.highest_stat_sum_team('goals', limit),
                        'Last game you scored a total of {value} goals. The game ranks at number {rank} in that regard.'),
                    (self.r.highest_stat_sum_team('assists', limit),
                        'Last game you got a total of {value} assists. The game ranks at number {rank} in that regard.'),
                    (self.r.highest_stat_sum_team('saves', limit),
                        'Last game you scored a total of {value} saves. The game ranks at number {rank} in that regard.'),
                    (self.r.highest_stat_sum_team('shots', limit),
                        'Last game you scored a total of {value} shots. The game ranks at number {rank} in that regard.'),
                    (self.r.diff_mvp_lvp('DESC', limit),
                        'Last game the difference between the MVP and LVP was {value} points. That is the {rank}. highest '
                        'difference.'),
                    (self.r.diff_mvp_lvp('ASC', limit),
                        'Last game the difference between the MVP and LVP was only {value} points. That is the {rank}. '
                        'lowest difference.'),
                    (self.r.most_solo_goals(limit),
                        'Last game had with {value} goals an usual amount of solo goals. The game ranks at number {rank} '
                        'in that regard.'),
                    (self.r.trend('score', 'MIN', limit),
                        'The point trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                        'total.'),
                    (self.r.trend('score', 'MAX', limit),
                        'The point trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                        'total.'),
                    (self.r.trend('goals', 'MIN', limit),
                        'The goal trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.'),
                    (self.r.trend('goals', 'MAX', limit),
                        'The goal trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                        'total.'),
                    (self.r.trend('assists', 'MIN', limit),
                        'The assist trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                        'total.'),
                    (self.r.trend('assists', 'MAX', limit),
                        'The assist trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                        'total.'),
                    (self.r.trend('saves', 'MIN', limit),
                        'The saves trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                        'total.'),
                    (self.r.trend('saves', 'MAX', limit),
                        'The saves trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                        'total.'),
                    (self.r.trend('shots', 'MIN', limit),
                        'The shots trend of {name} reached a value of {value}, which is the {rank}. lowest value in '
                        'total.'),
                    (self.r.trend('shots', 'MAX', limit),
                        'The shots trend of {name} reached a value of {value}, which is the {rank}. highest value in '
                        'total.')
                    ]
        # Iterate through data and check if last gameID appears # TODO Check only threshold
        for record in record_data:
            for index in range(0, limit):
                if record[0][index][2] == last_id:
                    facts.append((record[1].format(value=record[0][index][1], name=record[0][index][0], rank=index + 1), 4))

        return facts


    def record_session(self) -> list[tuple]:
        def record_games_per_session(limit: int = 1) -> list[Any]:
            self.c.execute('SELECT sessionID, wins+losses FROM sessions ORDER BY wins+losses DESC LIMIT %s', (limit,))
            return self.c.fetchall()

        facts = []
        # TODO: Session is close to being a record session
        session_count = self.q.session_count()
        session_limit = math.ceil(session_count)  # top 2%

        data = record_games_per_session(session_limit)
        next_milestone_rank = None
        next_milestone_value = None
        for rank in range(session_limit):
            if (rank + 1) % 5 == 0 and data[rank][0] != session_count:
                next_milestone_rank = rank + 1
                next_milestone_value = data[rank][1]
            if data[rank][0] == session_count and data[rank][1] > 10:
                facts.append((
                    f'You played {data[rank][1]} games this session. It ranks at spot number {rank + 1} in that regard.',
                    4))
                if next_milestone_value is not None and next_milestone_rank is not None:
                    games_to_reach_milestone = next_milestone_value - data[rank][1]
                    facts.append((
                        f'''To reach rank {next_milestone_rank} in games played this session, you need to 
                        play {1 if games_to_reach_milestone == 0 else games_to_reach_milestone} more games.''',
                        4))
        return facts


    # X has double the amount of Y, also session/season based
    def outclassed(self) -> list[tuple]:
        facts = []
        return facts


    # 'At least 1' streak in Goals/Assists/Saves
    def at_least_1_streak(self) -> list[tuple]:
        facts = []
        return facts


    # Streak of stats
    def streak(self) -> list[tuple]:
        # MVP/LVP streaks
        # x goals in succession
        facts = []
        return facts
    
    def game_amount_this_month(self) -> int:
        #SELECT COUNT(*) FROM games WHERE 
        #DATE_FORMAT(date,'%m') = DATE_FORMAT(CURDATE(),'%m') AND 
        #DATE_FORMAT(date,'%Y') = DATE_FORMAT(CURDATE(),'%Y')""")
        self.c.execute("SELECT COUNT(*) FROM games WHERE MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE())")
        return self.c.fetchone()[0]