import smtplib
import pytest
from unittest.mock import patch
from app.core import EmptyNotification, SenderNotAuthenticated, RecipientRefused, NotifierUnreachable
from app.notifier import EmailNotifier
from app.schemas import NotifierInput, DetectionNotifyByUser, Criteria

SMTP_TARGET = "app.notifier.email_notifier.smtplib.SMTP"

ONE_ITEM = [("Fone Bluetooth", 123456, Criteria.LOWEST_PRICE)]
TWO_ITEMS = ONE_ITEM + [("Mouse Sem Fio", 9990, Criteria.LOWER_BOUND)]

@pytest.fixture
def make_notifier():
    def _make(items):
        detections = [DetectionNotifyByUser(detection_id=i, title=title, link=f"http://example.com/p{i}",
                                            price=price, criteria=criteria)
                      for i, (title, price, criteria) in enumerate(items, start=1)]
        return EmailNotifier(NotifierInput(user_id=1, user_email="fred@example.com",
                                           user_name="Fred", items=detections))
    return _make

def test_empty_items_rejected(make_notifier):
    with pytest.raises(EmptyNotification):
        make_notifier([])

def test_subject_one_item(make_notifier):
    notifier = make_notifier(ONE_ITEM)
    assert notifier._email_subject() == "Seu produto: Fone Bluetooth está custando R$ 1.234,56."

def test_subject_many_items(make_notifier):
    notifier = make_notifier(TWO_ITEMS)
    assert notifier._email_subject() == "Produtos que você acompanha estão com bons preços."

def test_body_one_item(make_notifier):
    notifier = make_notifier(ONE_ITEM)
    body = notifier._email_body()
    assert body.startswith("Olá Fred,\n")
    assert "um produto cadastrado" in body
    assert "O item Fone Bluetooth está custando R$ 1.234,56" in body
    assert f"link: {notifier.items[0].link}" in body

def test_body_many_items(make_notifier):
    notifier = make_notifier(TWO_ITEMS)
    body = notifier._email_body()
    assert "alguns produtos cadastrados" in body
    for item in notifier.items:
        assert f"O item {item.title} está custando" in body
        assert f"link: {item.link}" in body

@pytest.mark.parametrize("criteria, message", [
    (Criteria.LOWEST_PRICE, EmailNotifier._LOWEST_PRICE_MSG),
    (Criteria.LOWER_BOUND, EmailNotifier._LOWER_BOUND_MSG),
])

def test_body_criteria_message(make_notifier, criteria, message):
    notifier = make_notifier([("Fone Bluetooth", 123456, criteria)])
    assert f"R$ 1.234,56{message}\n" in notifier._email_body()

@pytest.mark.parametrize("criteria", list(Criteria))
def test_every_criteria_has_message(make_notifier, criteria):
    notifier = make_notifier([("Fone Bluetooth", 123456, criteria)])
    assert notifier._get_criteria_msg(criteria) != "."

def test_send_message_success(make_notifier):
    notifier = make_notifier(ONE_ITEM)
    with patch(SMTP_TARGET) as mock_smtp:
        notifier.send_message()
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
    connection = mock_smtp.return_value.__enter__.return_value
    connection.starttls.assert_called_once()
    connection.login.assert_called_once()
    connection.send_message.assert_called_once()
    msg = connection.send_message.call_args.args[0]
    assert msg["To"] == "fred@example.com"
    assert msg["Subject"] == notifier._email_subject()

@pytest.mark.parametrize("where, error, expected", [
    ("login", smtplib.SMTPAuthenticationError(535, b"bad credentials"), SenderNotAuthenticated),
    ("send_message", smtplib.SMTPRecipientsRefused({}), RecipientRefused),
    ("connect", ConnectionRefusedError(), NotifierUnreachable),
])
def test_send_message_translates_errors(make_notifier, where, error, expected):
    notifier = make_notifier(ONE_ITEM)
    with patch(SMTP_TARGET) as mock_smtp:
        if where == "connect":
            mock_smtp.side_effect = error
        else:
            connection = mock_smtp.return_value.__enter__.return_value
            getattr(connection, where).side_effect = error
        with pytest.raises(expected):
            notifier.send_message()
