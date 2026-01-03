import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from unittest.mock import MagicMock, patch

from demos.recorded_moves import cli_main, main


def test_cli_main_default():
    with patch("argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.dataset = None
        mock_args.library = "dance"
        mock_parser.return_value.parse_args.return_value = mock_args
        with patch("demos.recorded_moves.main") as mock_main:
            cli_main()
            mock_main.assert_called_once_with(
                "pollen-robotics/reachy-mini-dances-library"
            )


def test_cli_main_dataset():
    with patch("argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.dataset = "my/dataset"
        mock_args.library = "dance"
        mock_parser.return_value.parse_args.return_value = mock_args
        with patch("demos.recorded_moves.main") as mock_main:
            cli_main()
            mock_main.assert_called_once_with("my/dataset")


def test_main():
    mock_reachy = MagicMock()
    mock_recorded_moves = MagicMock()
    mock_recorded_moves.list_moves.return_value = ["move1", "move2"]
    mock_move = MagicMock()
    mock_move.description = "A test move"
    mock_recorded_moves.get.side_effect = [mock_move, KeyboardInterrupt]

    with patch("demos.recorded_moves.ReachyMini", return_value=mock_reachy):
        with patch(
            "demos.recorded_moves.RecordedMoves", return_value=mock_recorded_moves
        ):
            main("dummy_path")

    mock_recorded_moves.list_moves.assert_called_once()
    mock_recorded_moves.get.assert_any_call("move1")
    mock_reachy.__enter__.return_value.play_move.assert_called_once_with(
        mock_move, initial_goto_duration=1.0
    )
