from src.services.schedule_generator import ScheduleGenerator


def main():
    teams = [
        "Team 01",
        "Team 02",
        "Team 03",
        "Team 04",
        "Team 05",
        "Team 06",
        "Team 07",
        "Team 08",
        "Team 09",
        "Team 10",
        "Team 11",
        "Team 12",
    ]

    generator = ScheduleGenerator()
    schedule = generator.generate_double_round_robin(teams)

    print("Spielplan erzeugt")
    print(f"Spieltage: {len(schedule)}")
    print()

    total_matches = 0

    for matchday in schedule:
        print(f"Spieltag {matchday['matchday']}")

        for home, away in matchday["matches"]:
            print(f"  {home} - {away}")
            total_matches += 1

        print()

    print(f"Spiele gesamt: {total_matches}")


if __name__ == "__main__":
    main()