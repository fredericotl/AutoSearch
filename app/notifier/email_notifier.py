import socket
from app.notifier.base import Notifier
import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.core.exceptions import  SenderNotAuthenticated, NotifierUnreachable,RecipientRefused
from app.schemas.price import Criteria
import logging

logger = logging.getLogger(__name__)

class EmailNotifier(Notifier):
    _SENDER_EMAIL = settings.sender_email
    _SENDER_PASSWORD = settings.sender_password
    _LOWEST_PRICE_MSG = ", é o preço mais baixo do último ano."
    _LOWER_BOUND_MSG = ", esse preço está bem abaixo do que costuma custar."


    def _email_body(self):
        if not self._is_one_item():
            intro = (f"Olá {self.receiver_name},\n"
                     f"Observamos que alguns produtos cadastrados que você acompanha estão com preços mais baixos:\n")
        else:
            intro = (f"Olá {self.receiver_name},\n"
                     f"Observamos que um produto cadastrado que você acompanha está com preço mais baixo:\n")
        infos = ""
        for item in self.items:
            infos += (f"O item {item.title} está custando {self.price_str(item.price)}{self._get_criteria_msg(item.criteria)}\n"
                      f"link: {item.link}\n")
        return intro + infos

    def _email_subject(self):
        if not self._is_one_item():
            return f"Produtos que você acompanha estão com bons preços."
        else:
            return f"Seu produto: {self.items[0].title} está custando {self.price_str(self.items[0].price)}."

    def send_message(self):
        msg = EmailMessage()
        msg["Subject"] = self._email_subject()
        msg["From"] = self._SENDER_EMAIL
        msg["To"] = self.receiver_email
        msg.set_content(self._email_body())
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()
                connection.login(user=self._SENDER_EMAIL, password=self._SENDER_PASSWORD)
                connection.send_message(msg)
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPSenderRefused) as e:
            raise SenderNotAuthenticated(f"{type(e).__name__}: {e}") from e
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, ConnectionRefusedError,
                socket.gaierror, TimeoutError) as e:
            raise NotifierUnreachable(f"{type(e).__name__}: {e}") from e
        except smtplib.SMTPRecipientsRefused as e:
            raise RecipientRefused(f"{type(e).__name__}: {e}") from e
        except OSError as e:
            raise NotifierUnreachable(f"{type(e).__name__}: {e}") from e

    def _get_criteria_msg(self, criteria: Criteria):
        if criteria == Criteria.LOWEST_PRICE:
            return self._LOWEST_PRICE_MSG
        elif criteria == Criteria.LOWER_BOUND:
            return self._LOWER_BOUND_MSG
        logger.warning("criteria without message: %s", criteria)
        return "."

