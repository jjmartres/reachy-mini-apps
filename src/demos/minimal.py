"""A minimal demonstration of the Reachy Mini SDK's capabilities.

This script connects to the robot and performs a simple, continuous
oscillation of its head (pitch) and antennas. It's a great way to verify
that the connection to the robot is working correctly.

Example:
    To run this demo:

    $ uv run minimal-demo
"""

import time
import argparse

import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def main() -> None:
    """Connects to Reachy and performs a head and antenna oscillation loop."""
    with ReachyMini(media_backend="no_media") as mini:
        mini.goto_target(create_head_pose(), antennas=[0.0, 0.0], duration=1.0)
        try:
            while True:
                t = time.time()

                antennas_offset = np.deg2rad(20 * np.sin(2 * np.pi * 0.5 * t))
                pitch = np.deg2rad(10 * np.sin(2 * np.pi * 0.5 * t))

                head_pose = create_head_pose(
                    roll=0.0,
                    pitch=pitch,
                    yaw=0.0,
                    degrees=False,
                    mm=False,
                )
                mini.set_target(
                    head=head_pose, antennas=[antennas_offset, antennas_offset]
                )
        except KeyboardInterrupt:
            print("\nDemo interrupted by user.")


def cli_main():
    """Parses command-line arguments and runs the main demo."""
    parser = argparse.ArgumentParser()
    parser.description = (
        "A simple demo that makes the robot's head and antennas oscillate."
    )
    main()


if __name__ == "__main__":
    cli_main()
