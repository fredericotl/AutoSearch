from app.schemas import NotifierInput, CreateError, ErrorSource
from app.notifier import EmailNotifier
from app.core.exeptions import (NotifierFail, RecipientRefused, EmptyNotification, SenderNotAuthenticated,
                                NotifierUnreachable)
from app.db.session import SessionLocal
from app.services import get_pendent_detections_by_user, mark_detections_sent, save_error

class NotifierTask:

    def _get_notifiers_inputs(self)-> list[NotifierInput]:
        db = SessionLocal()
        try:
            list_notifiers = get_pendent_detections_by_user(db)
            return list_notifiers
        finally:
            db.close()

    def run(self):
        all_notifiers = self._get_notifiers_inputs()
        for notification in all_notifiers:
            db = SessionLocal()
            try:
                notifier = EmailNotifier(notification)
                notifier.send_message()
                mark_detections_sent(db, notification.itens)
                db.commit()
            except (RecipientRefused, EmptyNotification) as e:
                error = CreateError(source=ErrorSource.NOTIFIER,
                                    error_type= type(e).__name__,
                                    user_id= notification.user_id,
                                    message= str(e)
                                    )
                save_error(db,error)
                db.commit()
            except (SenderNotAuthenticated, NotifierUnreachable) as e:
                error = CreateError(source=ErrorSource.NOTIFIER,
                                    error_type= type(e).__name__,
                                    message= str(e)
                                    )
                save_error(db,error)
                db.commit()
                break
            except NotifierFail as e:
                error = CreateError(source=ErrorSource.NOTIFIER,
                                    error_type=type(e).__name__,
                                    message=str(e)
                                    )
                save_error(db, error)
                db.commit()
            finally:
                db.close()

