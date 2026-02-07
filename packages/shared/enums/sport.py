from enum import Enum


class Sport(str, Enum):
    SOCCER = "soccer"
    NBA = "nba"
    NHL = "nhl"
    TENNIS = "tennis"


class League(str, Enum):
    # Soccer
    EPL = "epl"
    LA_LIGA = "la_liga"
    BUNDESLIGA = "bundesliga"
    SERIE_A = "serie_a"
    LIGUE_1 = "ligue_1"
    CHAMPIONS_LEAGUE = "champions_league"
    MLS = "mls"

    # NBA
    NBA = "nba"

    # NHL
    NHL = "nhl"

    # Tennis
    ATP = "atp"
    WTA = "wta"
    GRAND_SLAM = "grand_slam"

    @classmethod
    def for_sport(cls, sport: Sport) -> list["League"]:
        mapping: dict[Sport, list["League"]] = {
            Sport.SOCCER: [
                cls.EPL, cls.LA_LIGA, cls.BUNDESLIGA, cls.SERIE_A,
                cls.LIGUE_1, cls.CHAMPIONS_LEAGUE, cls.MLS,
            ],
            Sport.NBA: [cls.NBA],
            Sport.NHL: [cls.NHL],
            Sport.TENNIS: [cls.ATP, cls.WTA, cls.GRAND_SLAM],
        }
        return mapping.get(sport, [])
