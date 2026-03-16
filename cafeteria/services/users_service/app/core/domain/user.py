from uuid import UUID, uuid4


class User:
    def __init__(self, display_name: str):
        if not display_name or not display_name.strip():
            raise ValueError("Display name cannot be empty!")
        self.id: UUID = uuid4()
        self.display_name: str = display_name.strip()
