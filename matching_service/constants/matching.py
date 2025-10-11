from enum import Enum


class MatchingCriteriaEnum(str, Enum):
    TOPIC = "topic"
    DIFFICULTY = "difficulty"
    LANGUAGE = "language"
    PRIMARY_LANG = "prilanguage"
    SECONDARY_LANG = "seclanguage"

EXPIRATION_DURATION = 60
