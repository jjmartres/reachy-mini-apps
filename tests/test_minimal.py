import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from unittest.mock import MagicMock, patch

import numpy as np

from demos.minimal import main, cli_main


def test_main():
    # Mock ReachyMini and its context manager
    mock_mini = MagicMock()
    mock_reachy_mini = MagicMock()
    mock_reachy_mini.return_value.__enter__.return_value = mock_mini

    # Mock create_head_pose
    mock_create_head_pose = MagicMock()

    # Mock time.time to control the loop and exit after 3 iterations
    t_values = [0.0, 0.5, 1.0]
    time_mock = MagicMock(side_effect=t_values + [KeyboardInterrupt])

    with patch("demos.minimal.ReachyMini", mock_reachy_mini):
        with patch("demos.minimal.create_head_pose", mock_create_head_pose):
            with patch("time.time", time_mock):
                main()

    # Check that ReachyMini was initialized
    mock_reachy_mini.assert_called_once_with(media_backend="no_media")

    # Check that the initial position was set
    mock_create_head_pose.assert_any_call()  # Called once for the initial pose
    mock_mini.goto_target.assert_called_once()

    # Check the animation loop
    assert time_mock.call_count == len(t_values) + 1
    assert mock_mini.set_target.call_count == len(t_values)

    # Check the calls to create_head_pose and set_target
    for t in t_values:
        antennas_offset = np.deg2rad(20 * np.sin(2 * np.pi * 0.5 * t))
        pitch = np.deg2rad(10 * np.sin(2 * np.pi * 0.5 * t))
        mock_create_head_pose.assert_any_call(
            roll=0.0, pitch=pitch, yaw=0.0, degrees=False, mm=False
        )
        mock_mini.set_target.assert_any_call(
            head=mock_create_head_pose.return_value,
            antennas=[antennas_offset, antennas_offset],
        )


@patch("demos.minimal.main")
def test_cli_main(mock_main: MagicMock):
    """Tests that cli_main calls the main function."""
    cli_main()
    mock_main.assert_called_once()
