"""Plays a specific sequence of pre-recorded moves on the Reachy Mini robot.

This script connects to the robot, loads a specified set of moves from a
local or Hugging Face dataset, and plays them in the provided order.

Example:
    To play the '''simple_nod''' and '''yeah_nod''' moves from the '''dance''' library:

    $ python3 src/demos/play_move_set.py -l dance --moves simple_nod yeah_nod
"""

import argparse
import bisect
import json
import os
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import numpy.typing as npt
from huggingface_hub import snapshot_download
from huggingface_hub.errors import RepositoryNotFoundError

from reachy_mini import ReachyMini
from reachy_mini.motion.move import Move
from reachy_mini.utils.interpolation import linear_pose_interpolation

# The following code is adapted from reachy_mini.motion.recorded_move
# to correctly handle local paths.


def lerp(v0: float, v1: float, alpha: float) -> float:
    """Linear interpolation between two values.

    Args:
        v0: The starting value.
        v1: The ending value.
        alpha: The interpolation factor, typically between 0.0 and 1.0.

    Returns:
        The interpolated value.
    """
    return v0 + alpha * (v1 - v0)


class CustomRecordedMove(Move):
    """Represents a single recorded move with trajectory and metadata.

    This class holds the keyframes, timestamps, and description for a single
    animation. It provides a method to evaluate the robot'''s joint positions at
    any given time within the animation'''s duration.

    Attributes:
        description: A human-readable description of the move.
        timestamps: A list of timestamps for each keyframe in the move.
        trajectory: The raw trajectory data for all joints.
        dt: The time delta between keyframes.
    """

    def __init__(self, move: Dict[str, Any], sound_path: Optional[Path] = None) -> None:
        """Initializes the CustomRecordedMove instance.

        Args:
            move: A dictionary containing the move data, including description,
                timestamps, and trajectory.
            sound_path: An optional path to a sound file to be played with the move.
        """
        self.move = move
        self._sound_path = sound_path

        self.description: str = self.move["description"]
        self.timestamps: List[float] = self.move["time"]
        self.trajectory: List[Dict[str, List[List[float]] | List[float] | float]] = (
            self.move["set_target_data"]
        )

        self.dt: float = (self.timestamps[-1] - self.timestamps[0]) / len(
            self.timestamps
        )

    @property
    def duration(self) -> float:
        """Get the duration of the recorded move in seconds."""
        return len(self.trajectory) * self.dt

    @property
    def sound_path(self) -> Optional[Path]:
        """Get the sound path associated with the move, if any."""
        return self._sound_path

    def evaluate(
        self, t: float
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], float]:
        """Evaluates the move'''s joint positions at a specific time.

        This method calculates the interpolated position of the head, antennas,
        and body for a given point in time within the move'''s duration.

        Args:
            t: The time (in seconds) at which to evaluate the move.

        Returns:
            A tuple containing:
                - head: The 4x4 homogeneous matrix for the head'''s pose.
                - antennas: A numpy array with the target positions for the antennas (in radians).
                - body_yaw: The target angle for the body yaw (in radians).

        Raises:
            Exception: If the evaluation time `t` is beyond the move'''s duration.
        """
        if t > self.timestamps[-1]:
            raise Exception("Tried to evaluate recorded move beyond its duration.")

        index = bisect.bisect_right(self.timestamps, t)
        idx_prev = index - 1 if index > 0 else 0
        idx_next = index if index < len(self.timestamps) else idx_prev

        t_prev = self.timestamps[idx_prev]
        t_next = self.timestamps[idx_next]

        if t_next == t_prev:
            alpha = 0.0
        else:
            alpha = (t - t_prev) / (t_next - t_prev)

        head_prev = np.array(self.trajectory[idx_prev]["head"], dtype=np.float64)
        head_next = np.array(self.trajectory[idx_next]["head"], dtype=np.float64)
        antennas_prev: List[float] = self.trajectory[idx_prev]["antennas"]  # type: ignore[assignment]
        antennas_next: List[float] = self.trajectory[idx_next]["antennas"]  # type: ignore[assignment]
        body_yaw_prev: float = self.trajectory[idx_prev].get("body_yaw", 0.0)  # type: ignore[assignment]
        body_yaw_next: float = self.trajectory[idx_next].get("body_yaw", 0.0)  # type: ignore[assignment]

        antennas_joints = np.array(
            [
                lerp(pos_prev, pos_next, alpha)
                for pos_prev, pos_next in zip(antennas_prev, antennas_next)
            ],
            dtype=np.float64,
        )
        body_yaw = lerp(body_yaw_prev, body_yaw_next, alpha)
        head_pose = linear_pose_interpolation(head_prev, head_next, alpha)

        return head_pose, antennas_joints, body_yaw


class CustomRecordedMoves:
    """Loads and manages a library of recorded moves from a dataset.

    This class can load moves from either a local directory or a Hugging Face
    dataset. It scans for `.json` move files and their corresponding `.wav`
    sound files.
    """

    def __init__(self, dataset_path: str):
        """Initializes the move loader.

        This involves checking if the dataset_path is a local directory or
        a Hugging Face repository, then loading the move files.

        Args:
            dataset_path: The path to a local directory or the ID of a
                Hugging Face dataset repository.
        """
        self.dataset_path = dataset_path

        if os.path.isdir(self.dataset_path):
            self.local_path = self.dataset_path
        else:
            try:
                self.local_path = snapshot_download(
                    self.dataset_path, repo_type="dataset"
                )
            except RepositoryNotFoundError:
                print(
                    f"Error: Could not find repository '{self.dataset_path}' on Hugging Face Hub or locally."
                )
                # So that the script doesn't crash later
                self.local_path = ""

        self.moves: Dict[str, Any] = {}
        self.sounds: Dict[str, Optional[Path]] = {}

        if self.local_path:
            self.process()

    def process(self) -> None:
        """Finds and processes all move (.json) and sound (.wav) files.

        This method populates the internal `moves` and `sounds` dictionaries
        by scanning the local dataset directory.
        """
        move_paths_tmp = glob(f"{self.local_path}/*.json")
        move_paths = [Path(move_path) for move_path in move_paths_tmp]
        for move_path in move_paths:
            move_name = move_path.stem

            with open(move_path, "r") as f:
                move = json.load(f)
            self.moves[move_name] = move

            sound_path = move_path.with_suffix(".wav")
            self.sounds[move_name] = None

            if os.path.exists(sound_path):
                self.sounds[move_name] = sound_path

    def get(self, move_name: str) -> CustomRecordedMove:
        """Retrieves a specific move by its name.

        Args:
            move_name: The name of the move to retrieve (without file extension).

        Returns:
            A CustomRecordedMove instance for the requested move.

        Raises:
            ValueError: If the requested move_name is not found in the library.
        """
        if move_name not in self.moves:
            raise ValueError(
                f"Move {move_name} not found in recorded moves library {self.dataset_path}"
            )

        return CustomRecordedMove(self.moves[move_name], self.sounds[move_name])

    def list_moves(self) -> List[str]:
        """Lists the names of all moves available in the loaded library.

        Returns:
            A list of strings, where each string is the name of a move.
        """
        if not self.local_path:
            return []
        return list(self.moves.keys())


# Original script starts here, adapted for the custom classes.

LIBRARY_DATASETS = {
    "dance": "datasets/dances",
    "emotions": "datasets/emotions",
}


def main(dataset_path: str, moves_to_play: List[str]) -> None:
    """Connects to Reachy Mini and plays a specified sequence of moves.

    Args:
        dataset_path: The path to the dataset (local or Hugging Face).
        moves_to_play: A list of move names to be played in sequence.
    """
    recorded_moves = CustomRecordedMoves(dataset_path)
    available_moves = recorded_moves.list_moves()

    if not available_moves:
        print("No moves found. Exiting.")
        return

    # Validate that all requested moves are available
    for move_name in moves_to_play:
        if move_name not in available_moves:
            print(f"Error: Move '{move_name}' not found in the dataset.")
            print(f"Available moves are: {', '.join(available_moves)}")
            return

    print("Connecting to Reachy Mini...")
    with ReachyMini() as reachy:
        print("Connection successful! Starting move sequence...\n")
        try:
            for move_name in moves_to_play:
                move = recorded_moves.get(move_name)
                print(f"Playing move: {move_name}: {move.description}\n")
                reachy.play_move(move, initial_goto_duration=1.0)
            print("Move sequence finished.")

        except KeyboardInterrupt:
            print("\nSequence interrupted by user. Shutting down.")


def cli_main():
    """Parses command-line arguments and runs the main demo."""
    parser = argparse.ArgumentParser(
        description="Play a specific set of moves for Reachy Mini from a local or HF dataset."
    )
    parser.add_argument(
        "-l",
        "--library",
        type=str,
        default="dance",
        choices=sorted(LIBRARY_DATASETS.keys()),
        help="Pick one of the local libraries (default: dance).",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        help="Local path or HF dataset id. Overrides --library when provided.",
    )
    parser.add_argument(
        "--moves",
        type=str,
        nargs="+",
        required=True,
        help="A list of move names to play in sequence.",
    )
    args = parser.parse_args()
    dataset_path = args.dataset or LIBRARY_DATASETS[args.library]
    main(dataset_path, args.moves)


if __name__ == "__main__":
    cli_main()
