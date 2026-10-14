class ProductNotFound(Exception):
    """Product ID does not exist"""
    pass


class ProductAlreadyExists(Exception):
    """Product already exists"""
    pass

class ScraperFail(Exception):
    """Scraper Fail"""
    pass

class ScraperUnavailable(ScraperFail):
    """Problem with internet connection"""
    pass

class ProductGone(ScraperFail):
    """product not found 404"""
    pass

class ScraperBlocked(ScraperFail):
    """antibot erros"""
    pass

class PriceNotFound(ScraperFail):
    """Price was not found by scraper"""
    pass

class UnsupportedScraper(ScraperFail):
    """No scrapper for this domain"""
    pass

class UserNotFound(Exception):
    """User does not exist"""
    pass

class UserNotFollow(Exception):
    """User does not follow the product"""
    pass

class UserAlreadyFollow(Exception):
    """User already follow the product"""
    pass

class WrongPassword(Exception):
    """Password is not correct"""
    pass

class NotifierFail(Exception):
    """Notifier failed to send emails"""
    pass

class SenderNotAuthenticated(NotifierFail):
    """Sender is not Authenticated"""
    pass

class NotifierUnreachable(NotifierFail):
    """Problem with internet connection"""
    pass

class RecipientRefused(NotifierFail):
    """User email validation error"""
    pass

class EmptyNotification(NotifierFail):
    """Notifier with 0 items."""
    pass

class InvalidInvite(Exception):
    """Invalid invite token"""
    pass

__all__ = ["ProductNotFound", "ScraperFail", "ScraperUnavailable", "ProductGone",
           "ScraperBlocked", "PriceNotFound", "UnsupportedScraper", "UserNotFound","UserNotFollow",
           "WrongPassword", "NotifierFail", "SenderNotAuthenticated", "NotifierUnreachable", "RecipientRefused",
           "EmptyNotification", "InvalidInvite", "ProductAlreadyExists", "UserAlreadyFollow"]
