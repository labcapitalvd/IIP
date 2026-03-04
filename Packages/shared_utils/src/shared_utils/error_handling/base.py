class BaseDomainError(Exception):
    status_code = 400
    message = "An error occurred"

    def __init__(self, message=None):
        # Use provided message or the class-level default
        self.message = message or self.message
        super().__init__(self.message)
