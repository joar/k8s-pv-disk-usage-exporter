import attr


class Loggable:
    def __structlog__(self):
        if attr.has(type(self)):
            return attr.asdict(self)
        return self
