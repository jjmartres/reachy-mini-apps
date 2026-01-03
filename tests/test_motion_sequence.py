import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from unittest.mock import MagicMock, patch

from demos.motion_sequence import main


def test_main_loops():
    # Mock ReachyMini and its context manager
    mock_mini = MagicMock()
    mock_reachy_mini = MagicMock()
    mock_reachy_mini.return_value.__enter__.return_value = mock_mini

    def time_generator():
        t = 0
        for _ in range(100):
            yield t
            t += 0.1
        raise KeyboardInterrupt

    time_mock = MagicMock(side_effect=time_generator())

    with patch("demos.motion_sequence.ReachyMini", mock_reachy_mini):
        with patch("time.time", time_mock):
            main()

    # Check that ReachyMini was initialized
    mock_reachy_mini.assert_called_once_with(media_backend="no_media")

    # Check that the initial position was set
    mock_mini.goto_target.assert_called_once()

    # Check that set_target was called in each loop
    assert mock_mini.set_target.call_count > 6
