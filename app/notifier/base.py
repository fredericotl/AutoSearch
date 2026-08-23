from abc import ABC, abstractmethod
from app.schemas import NotifierInput
from app.core.exeptions import EmptyNotification

class Notifier(ABC):

    def __init__(self, receiver_info: NotifierInput):
        self.itens = receiver_info.itens
        self._is_zero_item()
        self.receiver_email = receiver_info.user_email
        self.receiver_name = receiver_info.user_name


    def _is_zero_item(self):
        if len(self.itens) == 0:
            raise EmptyNotification("Itens list is empty.")

    def _is_one_item(self):
        return len(self.itens) == 1

    @abstractmethod
    def send_message(self):
        pass