class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    def get_user_info(self):
        return {
            "user_id": self.user_id,
            "name": self.name
        }

    def update_name(self, new_name):
        self.name = new_name

    def __str__(self):
        return f"User({self.user_id}, {self.name})"