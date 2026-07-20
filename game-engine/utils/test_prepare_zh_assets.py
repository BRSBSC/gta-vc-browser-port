from pathlib import Path
import sys
import unittest


UTILS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(UTILS_DIR))

try:
    from prepare_zh_assets import EXPECTED_FILES, validate_assets
except ImportError as error:
    MISSING_IMPLEMENTATION = error
else:
    MISSING_IMPLEMENTATION = None


ASSET_DIR = UTILS_DIR.parent / "resources" / "zh"


class ZhAssetsTest(unittest.TestCase):
    def test_extracted_assets_contract(self) -> None:
        if MISSING_IMPLEMENTATION is not None:
            self.fail(
                f"{MISSING_IMPLEMENTATION.__class__.__name__}: "
                f"{MISSING_IMPLEMENTATION}"
            )

        summary = validate_assets(ASSET_DIR)
        file_names = sorted(
            path.name
            for path in ASSET_DIR.iterdir()
            if path.is_file()
        )

        self.assertEqual(file_names, sorted([*EXPECTED_FILES, "README.md"]))
        self.assertEqual(summary["table_count"], 79)
        self.assertGreater(summary["cjk_count"], 100)
        self.assertGreater(summary["main_cjk_count"], 0)


if __name__ == "__main__":
    unittest.main()
