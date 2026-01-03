import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
from huggingface_hub.errors import RepositoryNotFoundError

from demos.play_move_set import (
    CustomRecordedMove,
    CustomRecordedMoves,
    cli_main,
    main,
)

# A minimal valid move dictionary for testing
FAKE_MOVE_DATA = {
    "description": "A test move.",
    "time": [0.0, 1.0],
    "set_target_data": [
        {
            "head": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "antennas": [0.0, 0.0],
        },
        {
            "head": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "antennas": [0.1, 0.1],
        },
    ],
}

FAKE_MOVE_DATA_IDENTICAL_TIME = {
    "description": "A test move with identical timestamps.",
    "time": [0.5, 0.5],
    "set_target_data": [
        {
            "head": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "antennas": [0.0, 0.0],
        },
        {
            "head": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "antennas": [0.1, 0.1],
        },
    ],
}


@pytest.fixture
def local_dataset(tmp_path: Path) -> Path:
    """Creates a temporary local dataset for testing."""
    dataset_dir = tmp_path / "test_dataset"
    dataset_dir.mkdir()

    # Move with a corresponding sound file
    move1_path = dataset_dir / "move1.json"
    with open(move1_path, "w") as f:
        json.dump(FAKE_MOVE_DATA, f)
    (dataset_dir / "move1.wav").touch()

    # Move without a sound file
    move2_path = dataset_dir / "move2.json"
    with open(move2_path, "w") as f:
        json.dump(FAKE_MOVE_DATA, f)

    # Move with identical timestamps to test a specific branch
    move_identical_time_path = dataset_dir / "move_identical_time.json"
    with open(move_identical_time_path, "w") as f:
        json.dump(FAKE_MOVE_DATA_IDENTICAL_TIME, f)

    return dataset_dir


def test_custom_recorded_moves_local_path(local_dataset: Path):
    """Tests that CustomRecordedMoves loads local files and sounds correctly."""
    moves = CustomRecordedMoves(str(local_dataset))

    assert sorted(moves.list_moves()) == ["move1", "move2", "move_identical_time"]

    move1 = moves.get("move1")
    assert move1.description == "A test move."
    assert move1.sound_path is not None
    assert move1.sound_path.name == "move1.wav"

    move2 = moves.get("move2")
    assert move2.sound_path is None


def test_custom_recorded_moves_get_invalid(local_dataset: Path):
    """Tests that getting an invalid move raises a ValueError."""
    moves = CustomRecordedMoves(str(local_dataset))

    with pytest.raises(ValueError, match="Move invalid_move not found"):
        moves.get("invalid_move")


@patch("demos.play_move_set.snapshot_download")
def test_custom_recorded_moves_hf_path(
    mock_snapshot_download: MagicMock, local_dataset: Path
):
    """Tests that CustomRecordedMoves calls snapshot_download for a non-local path."""
    mock_snapshot_download.return_value = str(local_dataset)

    moves = CustomRecordedMoves("user/repo")

    mock_snapshot_download.assert_called_once_with("user/repo", repo_type="dataset")
    assert len(moves.list_moves()) == 3


@patch("demos.play_move_set.main")
def test_cli_main_parsing(mock_main: MagicMock):
    """Tests that cli_main parses arguments and calls main correctly."""
    with patch(
        "sys.argv", ["play-move-set", "--library", "dance", "--moves", "move1", "move2"]
    ):
        cli_main()

    mock_main.assert_called_once_with("datasets/dances", ["move1", "move2"])


@patch("demos.play_move_set.ReachyMini")
@patch("demos.play_move_set.CustomRecordedMoves")
def test_main_functionality(
    mock_recorded_moves: MagicMock, mock_reachy: MagicMock, local_dataset: Path
):
    """Tests the main logic of playing a move sequence."""
    mock_moves_instance = MagicMock()
    mock_moves_instance.list_moves.return_value = ["move1", "move2"]

    fake_move = MagicMock()
    fake_move.description = "A fake move."
    mock_moves_instance.get.return_value = fake_move

    mock_recorded_moves.return_value = mock_moves_instance

    mock_reachy_instance = MagicMock()
    mock_reachy.return_value.__enter__.return_value = mock_reachy_instance

    main(str(local_dataset), ["move1"])

    mock_recorded_moves.assert_called_once_with(str(local_dataset))
    mock_moves_instance.get.assert_called_once_with("move1")
    mock_reachy_instance.play_move.assert_called_once_with(
        fake_move, initial_goto_duration=1.0
    )


def test_main_move_not_found(capsys, local_dataset: Path):
    """Tests that main prints an error if a move is not found."""
    main(str(local_dataset), ["invalid_move"])

    captured = capsys.readouterr()
    assert "Error: Move 'invalid_move' not found" in captured.out


def test_custom_recorded_move_duration():
    """Tests the duration property of CustomRecordedMove."""
    move = CustomRecordedMove(FAKE_MOVE_DATA)
    assert move.duration == 1.0


def test_custom_recorded_move_evaluate():
    """Tests the evaluate method of CustomRecordedMove."""
    move = CustomRecordedMove(FAKE_MOVE_DATA)

    # Test at t=0.0 (start)
    head_pose, antennas, body_yaw = move.evaluate(0.0)
    assert np.array_equal(head_pose, np.eye(4))
    assert np.allclose(antennas, [0.0, 0.0])
    assert body_yaw == 0.0

    # Test at t=0.5 (midpoint)
    head_pose, antennas, body_yaw = move.evaluate(0.5)
    assert np.allclose(antennas, [0.05, 0.05])
    assert body_yaw == 0.0

    # Test raising exception beyond duration
    with pytest.raises(Exception, match="beyond its duration"):
        move.evaluate(1.1)


@patch("demos.play_move_set.snapshot_download")
def test_custom_recorded_moves_hf_path_not_found(
    mock_snapshot_download: MagicMock, capsys
):
    """Tests that a friendly error is printed when a HF repo is not found."""
    mock_snapshot_download.side_effect = RepositoryNotFoundError("Repo not found")

    moves = CustomRecordedMoves("user/nonexistent-repo")

    assert moves.list_moves() == []
    captured = capsys.readouterr()
    assert "Error: Could not find repository" in captured.out


def test_evaluate_identical_timestamps(local_dataset: Path):
    """Tests evaluate works correctly when timestamps are identical."""
    moves = CustomRecordedMoves(str(local_dataset))
    move = moves.get("move_identical_time")
    # This should execute the `alpha = 0.0` branch and not raise an error
    head_pose, antennas, body_yaw = move.evaluate(0.5)
    assert np.allclose(antennas, [0.1, 0.1])


@patch("demos.play_move_set.CustomRecordedMoves")
def test_main_no_moves_found(mock_recorded_moves: MagicMock, capsys):
    """Tests that main exits gracefully when no moves are found."""
    mock_moves_instance = MagicMock()
    mock_moves_instance.list_moves.return_value = []
    mock_recorded_moves.return_value = mock_moves_instance

    main("dummy_path", ["some_move"])

    captured = capsys.readouterr()
    assert "No moves found. Exiting." in captured.out


@patch("demos.play_move_set.ReachyMini")
def test_main_keyboard_interrupt(mock_reachy: MagicMock, local_dataset: Path, capsys):
    """Tests that main handles KeyboardInterrupt gracefully."""
    mock_reachy_instance = MagicMock()
    mock_reachy_instance.play_move.side_effect = KeyboardInterrupt
    mock_reachy.return_value.__enter__.return_value = mock_reachy_instance

    main(str(local_dataset), ["move1"])

    captured = capsys.readouterr()
    assert "Sequence interrupted by user." in captured.out
