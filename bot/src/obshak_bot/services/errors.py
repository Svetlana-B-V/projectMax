class UserError(Exception):
    """Ошибка бизнес-логики бота, текст которой можно показать пользователю как есть."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
