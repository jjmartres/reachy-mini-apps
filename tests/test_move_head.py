import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from demos.move_head import main


def test_main():
    mock_reachy = MagicMock()

    with patch("demos.move_head.ReachyMini", return_value=mock_reachy):
        # To avoid an infinite loop, we'll raise a KeyboardInterrupt
        # after the first call to set_target
        mock_reachy.__enter__.return_value.set_target.side_effect = [
            None,
            KeyboardInterrupt,
        ]
        main()

    mock_reachy.__enter__.return_value.set_target.assert_called()
