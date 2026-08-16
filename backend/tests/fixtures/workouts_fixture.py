"""Fixture containing 20 diverse structured workouts for compiler and DSL tests."""
from app.domain.workout_compiler import Step, RepeatBlock, StructuredWorkout

def generate_20_test_workouts() -> list[StructuredWorkout]:
    return [
        # 1. Bieg Proprogowy 4x5m Z4
        StructuredWorkout(
            name="Bieg Proprogowy 4x5m Z4",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="Z2", label="Rozgrzewka")]),
                RepeatBlock(reps=4, steps=[
                    Step(duration_min=5.0, target="102% Z4", label="Próg"),
                    Step(duration_min=3.0, target="55% Z1", label="Trucht regeneracyjny")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z1", label="Schłodzenie")])
            ]
        ),
        # 2. Kolarstwo Sweet Spot 3x12m
        StructuredWorkout(
            name="Kolarstwo Sweet Spot 3x12m",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="60% FTP", label="Rozgrzewka")]),
                RepeatBlock(reps=3, steps=[
                    Step(duration_min=12.0, target="90% FTP", label="SweetSpot"),
                    Step(duration_min=4.0, target="55% FTP", label="Odpoczynek")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="50% FTP", label="Schłodzenie")])
            ]
        ),
        # 3. Interwały VO2Max Bieg 5x3m
        StructuredWorkout(
            name="Interwały VO2Max Bieg 5x3m",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="Z2", label="Rozgrzewka")]),
                RepeatBlock(reps=5, steps=[
                    Step(duration_min=3.0, target="112% Z5", label="VO2Max"),
                    Step(duration_min=2.5, target="50% Z1", label="Marsz/Trucht")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z1", label="Schłodzenie")])
            ]
        ),
        # 4. Rower Over-Unders 4x4m
        StructuredWorkout(
            name="Rower Over-Unders 4x4m",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="60% FTP", label="Rozgrzewka")]),
                RepeatBlock(reps=4, steps=[
                    Step(duration_min=2.0, target="105% FTP", label="Over"),
                    Step(duration_min=2.0, target="95% FTP", label="Under")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="50% FTP", label="Schłodzenie")])
            ]
        ),
        # 5. Długi Bieg Tlenowy Z2
        StructuredWorkout(
            name="Długi Bieg Tlenowy Z2",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=10.0, target="Z1", label="Rozruch"),
                    Step(duration_min=70.0, target="Z2", label="Baza tlenowa"),
                    Step(duration_min=10.0, target="Z1", label="Schłodzenie")
                ])
            ]
        ),
        # 6. Sprinty Kolarskie 8x30s
        StructuredWorkout(
            name="Sprinty Kolarskie 8x30s",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="65% FTP", label="Rozgrzewka")]),
                RepeatBlock(reps=8, steps=[
                    Step(duration_min=0.5, target="150% FTP", label="Sprint Max"),
                    Step(duration_min=2.5, target="50% FTP", label="Regeneracja")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="50% FTP", label="Schłodzenie")])
            ]
        ),
        # 7. Regeneracyjny Bieg Z1
        StructuredWorkout(
            name="Regeneracyjny Bieg Z1 30 min",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=30.0, target="Z1", label="Spokojny trucht regeneracyjny")
                ])
            ]
        ),
        # 8. Pływanie Kraul Technika + Interwały
        StructuredWorkout(
            name="Pływanie Kraul Technika + Interwały",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z1", label="Rozgrzewka w wodzie")]),
                RepeatBlock(reps=10, steps=[
                    Step(duration_min=1.5, target="Z3", label="Pływanie kraul w tempie"),
                    Step(duration_min=0.5, target="Z1", label="Odpoczynek na nawrocie")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=5.0, target="Z1", label="Rozpływanie")])
            ]
        ),
        # 9. Trening Siłowy Kettlebell & Core
        StructuredWorkout(
            name="Trening Siłowy Kettlebell & Core",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=10.0, target="Z1", label="Mobilizacja i rozgrzewka"),
                    Step(duration_min=35.0, target="Siła", label="Seria główna KB Swing, Squats, Planks"),
                    Step(duration_min=5.0, target="Z1", label="Rozciąganie")
                ])
            ]
        ),
        # 10. Rower Piramida Z3-Z5
        StructuredWorkout(
            name="Rower Piramida Z3-Z5",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=15.0, target="60% FTP", label="Rozgrzewka"),
                    Step(duration_min=6.0, target="85% FTP", label="Z3 Tempo"),
                    Step(duration_min=4.0, target="100% FTP", label="Z4 Próg"),
                    Step(duration_min=2.0, target="115% FTP", label="Z5 VO2Max"),
                    Step(duration_min=4.0, target="100% FTP", label="Z4 Próg"),
                    Step(duration_min=6.0, target="85% FTP", label="Z3 Tempo"),
                    Step(duration_min=10.0, target="50% FTP", label="Schłodzenie")
                ])
            ]
        ),
        # 11. Bieg Proprogowy 3x10m Z4
        StructuredWorkout(
            name="Bieg Proprogowy 3x10m Z4",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="Z2", label="Rozgrzewka")]),
                RepeatBlock(reps=3, steps=[
                    Step(duration_min=10.0, target="100% Z4", label="Powtórzenie progowe"),
                    Step(duration_min=4.0, target="55% Z1", label="Trucht odpoczynkowy")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z1", label="Schłodzenie")])
            ]
        ),
        # 12. Rower Baza Z2 2h30m
        StructuredWorkout(
            name="Rower Baza Z2 2h30m",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=15.0, target="55% FTP", label="Rozgrzewka"),
                    Step(duration_min=120.0, target="70% FTP", label="Długi tlen kolarski"),
                    Step(duration_min=15.0, target="50% FTP", label="Schłodzenie")
                ])
            ]
        ),
        # 13. Bieg Podbiegi 10x45s
        StructuredWorkout(
            name="Bieg Podbiegi 10x45s",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="Z2", label="Rozgrzewka w terenie")]),
                RepeatBlock(reps=10, steps=[
                    Step(duration_min=0.75, target="Z5", label="Podbieg dynamiczny"),
                    Step(duration_min=1.5, target="Z1", label="Zejście w dół")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z1", label="Schłodzenie")])
            ]
        ),
        # 14. Kolarstwo Rampa Test FTP
        StructuredWorkout(
            name="Kolarstwo Rampa Test FTP",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=10.0, target="50% FTP", label="Rozgrzewka"),
                    Step(duration_min=5.0, target="75% FTP", label="Aktywacja")
                ]),
                RepeatBlock(reps=10, steps=[
                    Step(duration_min=1.0, target="+15W", label="Krok rampy")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="45% FTP", label="Schłodzenie")])
            ]
        ),
        # 15. Pływanie Interwały 8x50m
        StructuredWorkout(
            name="Pływanie Interwały 8x50m",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=8.0, target="Z1", label="Rozgrzewka")]),
                RepeatBlock(reps=8, steps=[
                    Step(duration_min=1.0, target="Z4", label="50m tempo sprint"),
                    Step(duration_min=0.5, target="Z1", label="Odpoczynek przy ściance")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=5.0, target="Z1", label="Rozpływanie")])
            ]
        ),
        # 16. Bieg Tempo 30m Z3
        StructuredWorkout(
            name="Bieg Tempo 30m Z3",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=10.0, target="Z2", label="Rozgrzewka"),
                    Step(duration_min=30.0, target="Z3", label="Ciągły bieg tempo"),
                    Step(duration_min=10.0, target="Z1", label="Schłodzenie")
                ])
            ]
        ),
        # 17. Rower Cadence Drills Z2
        StructuredWorkout(
            name="Rower Cadence Drills Z2",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="60% FTP", label="Rozgrzewka")]),
                RepeatBlock(reps=6, steps=[
                    Step(duration_min=4.0, target="72% FTP", label="Wysoka kadencja 105rpm"),
                    Step(duration_min=2.0, target="60% FTP", label="Niska kadencja 65rpm")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="50% FTP", label="Schłodzenie")])
            ]
        ),
        # 18. Trening Siłowy Biegacza
        StructuredWorkout(
            name="Trening Siłowy Biegacza",
            blocks=[
                RepeatBlock(reps=1, steps=[
                    Step(duration_min=10.0, target="Z1", label="Rozgrzewka ruchowa"),
                    Step(duration_min=30.0, target="Siła", label="Wspięcia na palce, RDL, Wykroki"),
                    Step(duration_min=10.0, target="Z1", label="Rozciąganie i rolowanie")
                ])
            ]
        ),
        # 19. Bieg Zmiany Tempa Fartlek 12x1m
        StructuredWorkout(
            name="Bieg Zmiany Tempa Fartlek 12x1m",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z2", label="Rozgrzewka")]),
                RepeatBlock(reps=12, steps=[
                    Step(duration_min=1.0, target="Z4", label="Mocne przyspieszenie"),
                    Step(duration_min=1.0, target="Z2", label="Swobodny bieg")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="Z1", label="Schłodzenie")])
            ]
        ),
        # 20. Kolarstwo Mikrointerwały 15x30s/30s
        StructuredWorkout(
            name="Kolarstwo Mikrointerwały 15x30s/30s",
            blocks=[
                RepeatBlock(reps=1, steps=[Step(duration_min=15.0, target="60% FTP", label="Rozgrzewka")]),
                RepeatBlock(reps=15, steps=[
                    Step(duration_min=0.5, target="130% FTP", label="Mikro-ON"),
                    Step(duration_min=0.5, target="50% FTP", label="Mikro-OFF")
                ]),
                RepeatBlock(reps=1, steps=[Step(duration_min=10.0, target="50% FTP", label="Schłodzenie")])
            ]
        )
    ]
