#!/usr/bin/env python3
"""
tests/test_analyze_genes.py
Tests unitaires automatises pour le script d'analyse des variants ClinVar (analyze_genes.py).

Verifie les regles metier:
1. Acceptation des variants Pathogenic, Likely pathogenic et Pathogenic/Likely pathogenic
2. Rejet des variants Benign, Likely benign, VUS et Conflicting
3. Dédoublonnage strict par VariationID pour chaque gène
4. Exclusion des symboles de gènes manquants ou ambigus (multi-gènes)
5. Tri décroissant du classement des gènes
6. Génération complète des cinq fichiers de sortie (CSV, JSON, PNG)
"""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Ajouter le dossier scripts au PYTHONPATH pour importation directe
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from analyze_genes import (
    ACCEPTED_SIGNIFICANCES,
    export_results,
    normalize_significance,
    process_dataset,
    validate_gene_symbol,
)


class TestClinVarAnalysisLogic(unittest.TestCase):
    """Tests unitaires sur les fonctions de filtrage et normalisation."""

    def test_normalize_significance_accepted(self):
        """Vérifie que les classifications pathogènes sont acceptées et normalisées."""
        for raw in ["Pathogenic", "pathogenic", "  Pathogenic  "]:
            accepted, norm = normalize_significance(raw)
            self.assertTrue(accepted)
            self.assertEqual(norm, "Pathogenic")

        for raw in ["Likely pathogenic", "likely pathogenic", "LIKELY PATHOGENIC"]:
            accepted, norm = normalize_significance(raw)
            self.assertTrue(accepted)
            self.assertEqual(norm, "Likely pathogenic")

        for raw in ["Pathogenic/Likely pathogenic", "pathogenic/likely pathogenic"]:
            accepted, norm = normalize_significance(raw)
            self.assertTrue(accepted)
            self.assertEqual(norm, "Pathogenic/Likely pathogenic")

    def test_normalize_significance_rejected(self):
        """Vérifie que les classifications non-pathogènes sont rejetées."""
        rejected_values = [
            "Benign",
            "Likely benign",
            "Benign/Likely benign",
            "Uncertain significance",
            "Conflicting classifications of pathogenicity",
            "not provided",
            "risk factor",
        ]
        for raw in rejected_values:
            accepted, _ = normalize_significance(raw)
            self.assertFalse(accepted, f"La valeur '{raw}' aurait du etre rejetee.")

    def test_validate_gene_symbol_valid(self):
        """Vérifie que les symboles HGNC standards et avec tirets sont acceptés."""
        for symbol in ["MYH7", "MYBPC3", "TNNT2", "NKX2-5", "NKX2-1"]:
            valid, norm, err = validate_gene_symbol(symbol)
            self.assertTrue(valid, f"Le symbole {symbol} devrait etre valide.")
            self.assertEqual(norm, symbol)
            self.assertEqual(err, "")

    def test_validate_gene_symbol_missing_or_ambiguous(self):
        """Vérifie le rejet des gènes manquants, tirets seuls ou multi-gènes (;)."""
        # Manquants
        for invalid in ["", "   ", "-", "na", "null", "none", "."]:
            valid, _, err = validate_gene_symbol(invalid)
            self.assertFalse(valid, f"'{invalid}' aurait du etre invalide.")
            self.assertIn("manquant", err.lower())

        # Ambigu / multi-gènes avec point-virgule
        multi_gene = "DNAAF3;DNAAF3-AS1;TNNI3"
        valid, _, err = validate_gene_symbol(multi_gene)
        self.assertFalse(valid)
        self.assertIn("ambigu", err.lower())


class TestDatasetProcessing(unittest.TestCase):
    """Tests sur le traitement complet d'un jeu synthétique de variants."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Création d'un mini TSV représentatif
        self.tsv_file = self.temp_path / "test_variants.tsv"
        self.fieldnames = [
            "VariationID", "GeneID", "GeneSymbol", "ClinicalSignificance",
            "PhenotypeList", "OriginSimple", "Assembly", "ReviewStatus",
            "NumberSubmitters", "RCVaccession", "AlleleID"
        ]

        self.rows = [
            # 1. Pathogène valide pour MYBPC3
            {
                "VariationID": "1001",
                "GeneID": "4607",
                "GeneSymbol": "MYBPC3",
                "ClinicalSignificance": "Pathogenic",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "criteria provided, multiple submitters",
                "NumberSubmitters": "5",
                "RCVaccession": "RCV0001",
                "AlleleID": "101",
            },
            # 2. Deuxième variant distinct pour MYBPC3
            {
                "VariationID": "1002",
                "GeneID": "4607",
                "GeneSymbol": "MYBPC3",
                "ClinicalSignificance": "Likely pathogenic",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "criteria provided, single submitter",
                "NumberSubmitters": "1",
                "RCVaccession": "RCV0002",
                "AlleleID": "102",
            },
            # 3. Doublon de VariationID pour MYBPC3 (doit etre dedoublonne)
            {
                "VariationID": "1001",
                "GeneID": "4607",
                "GeneSymbol": "MYBPC3",
                "ClinicalSignificance": "Pathogenic",
                "PhenotypeList": "Hypertrophic cardiomyopathy 1",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "criteria provided",
                "NumberSubmitters": "2",
                "RCVaccession": "RCV0003",
                "AlleleID": "103",
            },
            # 4. Variant Pathogène pour MYH7
            {
                "VariationID": "2001",
                "GeneID": "4625",
                "GeneSymbol": "MYH7",
                "ClinicalSignificance": "Pathogenic/Likely pathogenic",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "reviewed by expert panel",
                "NumberSubmitters": "8",
                "RCVaccession": "RCV0004",
                "AlleleID": "201",
            },
            # 5. Variant bénin (doit être rejeté)
            {
                "VariationID": "3001",
                "GeneID": "4625",
                "GeneSymbol": "MYH7",
                "ClinicalSignificance": "Benign",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "criteria provided",
                "NumberSubmitters": "3",
                "RCVaccession": "RCV0005",
                "AlleleID": "301",
            },
            # 6. Variant avec signification incertaine VUS (doit être rejeté)
            {
                "VariationID": "3002",
                "GeneID": "7137",
                "GeneSymbol": "TNNT2",
                "ClinicalSignificance": "Uncertain significance",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "criteria provided",
                "NumberSubmitters": "1",
                "RCVaccession": "RCV0006",
                "AlleleID": "302",
            },
            # 7. Symbole de gène manquant '-' (doit être rejeté)
            {
                "VariationID": "4001",
                "GeneID": "",
                "GeneSymbol": "-",
                "ClinicalSignificance": "Pathogenic",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "no assertion criteria provided",
                "NumberSubmitters": "1",
                "RCVaccession": "RCV0007",
                "AlleleID": "401",
            },
            # 8. Symbole de gène ambigu multi-gènes (doit être rejeté)
            {
                "VariationID": "5001",
                "GeneID": "1234;5678",
                "GeneSymbol": "TNNI3;DNAAF3",
                "ClinicalSignificance": "Likely pathogenic",
                "PhenotypeList": "Hypertrophic cardiomyopathy",
                "OriginSimple": "germline",
                "Assembly": "GRCh38",
                "ReviewStatus": "criteria provided",
                "NumberSubmitters": "1",
                "RCVaccession": "RCV0008",
                "AlleleID": "501",
            },
        ]

        with open(self.tsv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(self.rows)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_processing_counts_and_ranking(self):
        """Teste le décompte exact et le classement attendu."""
        results = process_dataset(self.tsv_file)

        # 8 lignes en entrée
        self.assertEqual(results["total_records"], 8)

        # Retenus attendus :
        # - VariationID 1001 (MYBPC3)
        # - VariationID 1002 (MYBPC3)
        # - VariationID 2001 (MYH7)
        # Total retenus = 3
        self.assertEqual(results["total_retained"], 3)
        self.assertEqual(results["total_excluded"], 5)

        # Classement : MYBPC3 (2 variants) > MYH7 (1 variant)
        ranking = results["ranking"]
        self.assertEqual(len(ranking), 2)

        self.assertEqual(ranking[0]["GeneSymbol"], "MYBPC3")
        self.assertEqual(ranking[0]["DistinctVariantCount"], 2)
        self.assertEqual(ranking[0]["Rank"], 1)

        self.assertEqual(ranking[1]["GeneSymbol"], "MYH7")
        self.assertEqual(ranking[1]["DistinctVariantCount"], 1)
        self.assertEqual(ranking[1]["Rank"], 2)

    def test_output_files_generation(self):
        """Vérifie que export_results crée tous les fichiers obligatoires."""
        results = process_dataset(self.tsv_file)
        out_dir = self.temp_path / "results_test"
        exported = export_results(results, out_dir, top_n=5, input_filename="test_variants.tsv")

        expected_files = [
            "gene_ranking.csv",
            "variants_hcm.csv",
            "excluded_variants.csv",
            "summary.json",
            "top_genes.png",
        ]

        for fname in expected_files:
            file_path = out_dir / fname
            self.assertTrue(file_path.exists(), f"Fichier manquant: {fname}")
            self.assertGreater(file_path.stat().st_size, 0, f"Fichier vide: {fname}")

        # Vérifier le contenu du JSON
        with open(out_dir / "summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
            self.assertEqual(summary["statistics"]["total_retained_variants"], 3)
            self.assertEqual(summary["statistics"]["unique_genes_count"], 2)
            self.assertIn("ClinicalSignificance", summary["scientific_scope_note"])


class TestCommandLineInterface(unittest.TestCase):
    """Test d'intégration du script analyze_genes.py via la ligne de commande."""

    def test_cli_execution(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            tsv_path = tmp_path / "sample.tsv"
            out_dir = tmp_path / "out"

            # Mini TSV avec en-tête valide et une ligne
            with open(tsv_path, "w", newline="", encoding="utf-8") as f:
                f.write("VariationID\tGeneID\tGeneSymbol\tClinicalSignificance\tPhenotypeList\tOriginSimple\tAssembly\tReviewStatus\tNumberSubmitters\tRCVaccession\tAlleleID\n")
                f.write("9999\t4607\tMYBPC3\tPathogenic\tHypertrophic cardiomyopathy\tgermline\tGRCh38\tcriteria provided\t1\tRCV009\t999\n")

            script_path = PROJECT_ROOT / "scripts" / "analyze_genes.py"
            cmd = [
                sys.executable,
                str(script_path),
                "--variants", str(tsv_path),
                "--output-dir", str(out_dir),
                "--top", "10",
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"Erreur CLI: {res.stderr}")
            self.assertTrue((out_dir / "gene_ranking.csv").exists())
            self.assertTrue((out_dir / "summary.json").exists())
            self.assertTrue((out_dir / "top_genes.png").exists())


if __name__ == "__main__":
    unittest.main()
