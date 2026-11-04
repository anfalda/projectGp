import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_FILE = ROOT / "results" / "summary.json"
README_FILE = ROOT / "README.md"


class TestResultsDocumentation(unittest.TestCase):

    @unittest.skipUnless(
        SUMMARY_FILE.exists(),
        "No generated summary.json available; run the pipeline first."
    )
    def test_readme_matches_generated_results(self):
        summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
        readme = README_FILE.read_text(encoding="utf-8")
        stats = summary["statistics"]

        total = stats["total_retained_variant_gene_associations"]
        input_records = stats["total_input_records"]
        excluded = stats["total_excluded_records"]

        self.assertIn(f"{input_records:,}".replace(",", " "), readme)
        self.assertIn(f"{total:,}".replace(",", " "), readme)
        self.assertIn(f"{excluded:,}".replace(",", " "), readme)

        for gene in summary["top_genes"][:10]:
            symbol = gene["GeneSymbol"]
            count = gene["DistinctVariantCount"]
            percentage = f'{gene["PercentageOfRetainedVariants"]:.2f}'.replace(".", ",")

            matching_rows = [
                line for line in readme.splitlines()
                if line.startswith("|") and f"**{symbol}**" in line
            ]

            self.assertEqual(
                len(matching_rows), 1,
                f"README must contain exactly one row for {symbol}"
            )

            cells = [cell.strip() for cell in matching_rows[0].split("|")]

            self.assertEqual(cells[4], f"**{count}**", f"Wrong count for {symbol}")
            self.assertEqual(
                cells[5], f"**{percentage} %**",
                f"Wrong percentage for {symbol}"
            )


if __name__ == "__main__":
    unittest.main()
