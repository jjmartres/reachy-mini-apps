import time
import argparse
import numpy as np
from reachy_mini import ReachyMini
from scipy.spatial.transform import Rotation as R


def main():
    """A simple demo that makes the robot's head draw a circle."""
    with ReachyMini(media_backend="no_media") as mini:
        try:
            while True:
                t = time.time()

                # Full circle in 5 seconds
                yaw = 2 * np.pi * t / 5

                # Create rotation matrix from yaw
                rot_mat = R.from_euler("xyz", [0, 0, yaw]).as_matrix()

                # Create 4x4 pose matrix
                pose = np.eye(4)
                pose[:3, :3] = rot_mat

                # Set the target
                mini.set_target(head=pose)
                time.sleep(0.01)

        except KeyboardInterrupt:
            pass


def cli_main():
    parser = argparse.ArgumentParser()
    parser.description = "A simple demo that makes the robot's head draw a circle."
    main()


if __name__ == "__main__":
    cli_main()
