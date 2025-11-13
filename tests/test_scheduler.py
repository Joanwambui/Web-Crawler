# tests/test_scheduler.py

import pytest
from unittest.mock import patch, MagicMock, ANY
from subprocess import CalledProcessError

# Import the function under test
from scheduler.daily_scheduler import run_crawler


# ---------------------------------------------------------
# TEST 1 — Ensure run_crawler runs both commands successfully
# ---------------------------------------------------------
@patch("scheduler.daily_scheduler.run")
def test_run_crawler_success(mock_run):
    # Simulate successful subprocess run
    mock_run.return_value = MagicMock()

    # Act
    run_crawler()

    # Assert: scrapy command called
    mock_run.assert_any_call(
        ["scrapy", "crawl", "book_spider"],
        check=True,
        cwd=ANY                  # ✔ use ANY here
    )

    # Assert: generate_report.py command called
    mock_run.assert_any_call(
        [ANY, ANY],              # sys.executable, REPORT_SCRIPT
        check=True
    )

    # Ensure exactly 2 subprocess runs
    assert mock_run.call_count == 2


# ---------------------------------------------------------
# TEST 2 — Verify CalledProcessError is handled gracefully
# ---------------------------------------------------------
@patch("scheduler.daily_scheduler.run")
def test_run_crawler_calledprocess_error(mock_run):
    mock_run.side_effect = CalledProcessError(1, "scrapy crawl book_spider")

    # Should NOT raise — errors are caught inside run_crawler()
    run_crawler()


# ---------------------------------------------------------
# TEST 3 — Verify generic exception is handled
# ---------------------------------------------------------
@patch("scheduler.daily_scheduler.run")
def test_run_crawler_generic_exception(mock_run):
    mock_run.side_effect = Exception("Unexpected failure")

    # Should NOT raise — handled inside run_crawler()
    run_crawler()
