from abc import ABC, abstractmethod
from app.schemas import NotifierInput
from app.core import EmptyNotification

class Notifier(ABC):

    def __init__(self, receiver_info: NotifierInput):
        self.items = receiver_info.items
        self._reject_empty()
        self.receiver_email = receiver_info.user_email
        self.receiver_name = receiver_info.user_name


    def _reject_empty(self):
        if len(self.items) == 0:
            raise EmptyNotification("Items list is empty.")

    def _is_one_item(self):
        return len(self.items) == 1

    @abstractmethod
    def send_message(self):
        pass

    @staticmethod
    def price_str(price: int, currency:str = "R$ "):
        units, cents = divmod(price, 100)
        units = f"{units:,}".replace(",", ".")
        return f"{currency}{units},{cents:02d}"