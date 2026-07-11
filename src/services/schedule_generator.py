class ScheduleGenerator:

    def generate_double_round_robin(self, teams):
        if len(teams) < 2:
            raise ValueError("Es werden mindestens 2 Mannschaften benötigt.")

        if len(teams) % 2 != 0:
            teams = teams + [None]

        first_round = self._generate_single_round(teams)
        second_round = self._generate_second_round(first_round)

        return first_round + second_round

    def _generate_single_round(self, teams):
        teams = teams.copy()

        matchdays = []
        team_count = len(teams)
        rounds = team_count - 1
        matches_per_round = team_count // 2

        for matchday in range(1, rounds + 1):
            matches = []

            for index in range(matches_per_round):
                home = teams[index]
                away = teams[team_count - 1 - index]

                if home is not None and away is not None:
                    if matchday % 2 == 0:
                        matches.append((away, home))
                    else:
                        matches.append((home, away))

            matchdays.append(
                {
                    "matchday": matchday,
                    "matches": matches,
                }
            )

            teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        return matchdays

    def _generate_second_round(self, first_round):
        second_round = []

        total_first_round_matchdays = len(first_round)

        for matchday_data in first_round:
            new_matchday_number = matchday_data["matchday"] + total_first_round_matchdays
            reversed_matches = []

            for home, away in matchday_data["matches"]:
                reversed_matches.append((away, home))

            second_round.append(
                {
                    "matchday": new_matchday_number,
                    "matches": reversed_matches,
                }
            )

        return second_round