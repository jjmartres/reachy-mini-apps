import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from demos.motion_sequence import main, cli_main


def test_main_loops():
    """Tests that the main loop runs through all motion sequences."""
    mock_mini = MagicMock()
    mock_reachy_mini = MagicMock()
    mock_reachy_mini.return_value.__enter__.return_value = mock_mini

    def time_generator():
        t = 0
        # Increased range to cover the full 15+ second animation loop
        for _ in range(200):
            yield t
            t += 0.1
        # Stop the infinite loop
        raise KeyboardInterrupt

    time_mock = MagicMock(side_effect=time_generator())
    sleep_mock = MagicMock()

    with patch("demos.motion_sequence.ReachyMini", mock_reachy_mini):
        with patch("time.time", time_mock):
            # Also mock sleep to make the test run faster
            with patch("time.sleep", sleep_mock):
                main()

    # Assertions
    mock_reachy_mini.assert_called_once_with(media_backend="no_media")
    mock_mini.goto_target.assert_called_once()
    # The full sequence has many calls to set_target
    assert mock_mini.set_target.call_count > 10


@patch("demos.motion_sequence.main")
def test_cli_main(mock_main: MagicMock):
    """Tests that cli_main calls the main function."""
    cli_main()
    mock_main.assert_called_once()
