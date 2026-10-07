import pytest
from unittest.mock import MagicMock
from app.workers import TasksRound


@pytest.fixture
def tasks_round():
    round_ = TasksRound()
    round_.scraper = MagicMock()
    round_.notifier = MagicMock()
    return round_


def test_round_runs_scraper_and_notifier(tasks_round):
    tasks_round.run()
    tasks_round.scraper.run.assert_called_once()
    tasks_round.notifier.run.assert_called_once()

def test_notifier_runs_even_if_scraper_breaks(tasks_round):
    tasks_round.scraper.run.side_effect = RuntimeError("scraping quebrado")
    with pytest.raises(RuntimeError):
        tasks_round.run()
    tasks_round.notifier.run.assert_called_once()