"""Makes the Reachy Mini's head move in a circular pattern.

This script demonstrates how to control the robot's head orientation
in real-time to create a continuous circular movement. It also shows how to
keep the robot's body stationary while the head is moving.

Example:
    To run this demo:

    $ uv run move-head
"""

import time
import argparse
import numpy as np
from reachy_mini import ReachyMini
from scipy.spatial.transform import Rotation as R


def main() -> None:
    """Connects to Reachy and makes the head draw a circle."""
    with ReachyMini(media_backend="no_media") as mini:
        try:
            while True:
                t = time.time()

                # Calculate yaw for a full circle in 5 seconds
                yaw = 2 * np.pi * t / 5

                # Create rotation matrix from yaw
                rot_mat = R.from_euler("xyz", [0, 0, yaw]).as_matrix()

                # Create 4x4 pose matrix
                pose = np.eye(4)
                pose[:3, :3] = rot_mat

                # Set the target for the head, keeping the body stationary.
                mini.set_target(head=pose, body_yaw=0.0)
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nDemo interrupted by user.")


def cli_main():
    """Parses command-line arguments and runs the main demo."""
    parser = argparse.ArgumentParser()
    parser.description = "A simple demo that makes the robot's head draw a circle."
    main()


if __name__ == "__main__":
    cli_main()
