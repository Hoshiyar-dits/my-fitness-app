from enum import Enum

class NutritionAccuracy(str, Enum):
    estimated = "estimated"  # guessed or looked up for a similar food
    verified = "verified"  # from the package label or a weighed portion
