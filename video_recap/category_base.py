from abc import ABC

class CategoryBase(ABC):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return super().__eq__(other)

    @staticmethod
    def get_category(name):
        if name == "movie":
            from .movie import Movie
            return Movie()
        elif name == "anime":
            from .anime import Anime
            return Anime()
        else:
            raise ValueError(f"Invalid category: {name}")