class ProductNotFound(Exception):
    """Product ID does not exist"""
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

class UserNotFollow(Exception):
    """User does not follow the product"""
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

