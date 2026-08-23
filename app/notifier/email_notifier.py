import socket
from app.notifier.base import Notifier
import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.core.exeptions import  SenderNotAuthenticated, NotifierUnreachable,RecipientRefused
class EmailNotifier(Notifier):
    _SENDER_EMAIL = settings.sender_email
    _SENDER_PASSWORD = settings.sender_password

    def _email_body(self):
        if not self._is_one_item():
            intro = (f"Olá {self.receiver_name},\n"
                     f"Alguns produtos cadastrados que você acompanha está com preço mais baixo que o normal:\n")
        else:
            intro = (f"Olá {self.receiver_name},\n"
                     f"Um produto cadastrado que você acompanha está com preço mais baixo que o normal:\n")
        infos = ""
        for item in self.itens:
            infos += (f"O item {item.title} está custando {(item.price/100)}.\n"
                      f"link: {item.link}\n")
        return intro + infos

    def _email_subject(self):
        if not self._is_one_item():
            return f"Alguns produtos que você acompanha estão com seu menor preço até agora."
        else:
            return f"Seu produto: {self.itens[0].title} está com seu menor preço até agora."

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