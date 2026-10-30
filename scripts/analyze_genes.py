#!/usr/bin/env python3
"""
scripts/analyze_genes.py
Analyse des variants ClinVar pour la cardiomyopathie hypertrophique (HCM/CMH).

Objectif:
Identifier les gènes concentrant le plus grand nombre de variants distincts
classés 'Pathogenic', 'Likely pathogenic' ou 'Pathogenic/Likely pathogenic'
dans ClinVar (assemblage GRCh38, origine germline).

Auteur: Etudiant 3 - Analyse Python
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Utilisation du backend Agg pour l'export graphique sans serveur X/affichage graphique
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ACCEPTED_SIGNIFICANCES = {
    "pathogenic": "Pathogenic",
    "likely pathogenic": "Likely pathogenic",
    "pathogenic/likely pathogenic": "Pathogenic/Likely pathogenic",
}

INVALID_GENE_SYMBOLS = {"", "-", "na", "null", "none", "."}


def normalize_significance(raw_sig: str) -> tuple[bool, str]:
    """
    Normalise la classification clinique et indique si elle est retenue.
    Retourne (est_retenu, valeur_normalisee).
    """
    cleaned = (raw_sig or "").strip()
    key = cleaned.lower()
    if key in ACCEPTED_SIGNIFICANCES:
        return True, ACCEPTED_SIGNIFICANCES[key]
    return False, cleaned


def validate_gene_symbol(raw_symbol: str) -> tuple[bool, str, str]:
    """
    Valide et normalise le symbole du gène selon les recommandations HGNC.
    Retourne (est_valide, symbole_normalise, raison_exclusion_si_invalide).
    """
    cleaned = (raw_symbol or "").strip()
    if not cleaned or cleaned.lower() in INVALID_GENE_SYMBOLS:
        return False, cleaned, "Symbole de gene manquant ou non specifie"

    # Gènes multiples / régions de délétion-duplication séparées par des points-virgules
    if ";" in cleaned:
        return False, cleaned, f"Symbole de gene ambigu (association multi-genes: {cleaned})"

    # Descriptions textuelles de remaniements complexes
    if " " in cleaned or "covers" in cleaned.lower():
        return False, cleaned, f"Annotation complexe non assimilable a un gene unique: {cleaned}"

    return True, cleaned, ""


def parse_arguments():
    """Analyse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Analyse des variants pathogenes de la cardiomyopathie hypertrophique dans ClinVar."
    )
    parser.add_argument(
        "--variants",
        required=True,
        type=Path,
        help="Chemin vers le fichier TSV filtre (ex: data/processed/hcm_variants_grch38.tsv)",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("results"),
        type=Path,
        help="Repertoire de destination des resultats (defaut: results)",
    )
    parser.add_argument(
        "--top",
        default=15,
        type=int,
        help="Nombre de premiers genes a afficher dans la figure (defaut: 15)",
    )
    return parser.parse_args()


def process_dataset(tsv_path: Path):
    """
    Lit le fichier TSV filtré, applique les critères d'acceptation,
    gère les doublons de VariationID et regroupe par gène.
    """
    if not tsv_path.is_file():
        raise FileNotFoundError(f"Fichier de variants introuvable: {tsv_path}")

    retained_variants = []
    excluded_variants = []
    seen_variants_by_gene = defaultdict(set)
    gene_to_variants = defaultdict(set)
    exclusion_reasons_counter = Counter()
    accepted_significances_counter = Counter()

    total_records = 0

    with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        expected_fields = {"VariationID", "GeneSymbol", "ClinicalSignificance"}
        if not expected_fields.issubset(set(reader.fieldnames or [])):
            missing = expected_fields - set(reader.fieldnames or [])
            raise ValueError(f"Colonnes manquantes dans le TSV: {missing}")

        for row in reader:
            total_records += 1
            variation_id = (row.get("VariationID") or "").strip()
            raw_gene = row.get("GeneSymbol", "")
            raw_sig = row.get("ClinicalSignificance", "")

            # 1. Vérification de la classification clinique (P / LP)
            is_sig_accepted, norm_sig = normalize_significance(raw_sig)
            if not is_sig_accepted:
                reason = f"Classification non retenue: '{norm_sig}'"
                exclusion_reasons_counter[reason] += 1
                excluded_variants.append({
                    "VariationID": variation_id,
                    "GeneID": row.get("GeneID", ""),
                    "GeneSymbol": raw_gene,
                    "ClinicalSignificance": raw_sig,
                    "Reason": reason,
                })
                continue

            # 2. Vérification et normalisation du symbole de gène
            is_gene_valid, norm_gene, gene_error = validate_gene_symbol(raw_gene)
            if not is_gene_valid:
                exclusion_reasons_counter[gene_error] += 1
                excluded_variants.append({
                    "VariationID": variation_id,
                    "GeneID": row.get("GeneID", ""),
                    "GeneSymbol": raw_gene,
                    "ClinicalSignificance": raw_sig,
                    "Reason": gene_error,
                })
                continue

            # 3. Dédoublonnage : un VariationID ne doit pas être compté deux fois pour le même gène
            if variation_id in seen_variants_by_gene[norm_gene]:
                reason = f"Doublon de VariationID ({variation_id}) pour le gene {norm_gene}"
                exclusion_reasons_counter[reason] += 1
                excluded_variants.append({
                    "VariationID": variation_id,
                    "GeneID": row.get("GeneID", ""),
                    "GeneSymbol": norm_gene,
                    "ClinicalSignificance": raw_sig,
                    "Reason": reason,
                })
                continue

            # Variant accepté et retenu
            seen_variants_by_gene[norm_gene].add(variation_id)
            gene_to_variants[norm_gene].add(variation_id)
            accepted_significances_counter[norm_sig] += 1

            row_copy = dict(row)
            row_copy["ClinicalSignificance"] = norm_sig
            row_copy["GeneSymbol"] = norm_gene
            retained_variants.append(row_copy)

    # Calcul du classement décroissant
    ranking = []
    total_retained = len(retained_variants)

    sorted_genes = sorted(
        gene_to_variants.items(),
        key=lambda item: (-len(item[1]), item[0])
    )

    for rank, (gene, var_set) in enumerate(sorted_genes, start=1):
        count = len(var_set)
        pct = (count / total_retained * 100.0) if total_retained > 0 else 0.0
        ranking.append({
            "Rank": rank,
            "GeneSymbol": gene,
            "DistinctVariantCount": count,
            "PercentageOfRetainedVariants": round(pct, 2),
        })

    return {
        "total_records": total_records,
        "total_retained": total_retained,
        "total_excluded": len(excluded_variants),
        "retained_variants": retained_variants,
        "excluded_variants": excluded_variants,
        "ranking": ranking,
        "exclusion_reasons": dict(exclusion_reasons_counter.most_common()),
        "accepted_significances": dict(accepted_significances_counter),
    }


def export_results(processed_data: dict, output_dir: Path, top_n: int, input_filename: str):
    """Exporte tous les fichiers de résultats attendus (CSV, JSON, PNG)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    ranking = processed_data["ranking"]
    retained_variants = processed_data["retained_variants"]
    excluded_variants = processed_data["excluded_variants"]
    total_retained = processed_data["total_retained"]

    # 1. results/gene_ranking.csv
    ranking_file = output_dir / "gene_ranking.csv"
    with open(ranking_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Rank", "GeneSymbol", "DistinctVariantCount", "PercentageOfRetainedVariants"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranking)

    # 2. results/variants_hcm.csv
    variants_file = output_dir / "variants_hcm.csv"
    with open(variants_file, "w", newline="", encoding="utf-8") as f:
        if retained_variants:
            fieldnames = list(retained_variants[0].keys())
        else:
            fieldnames = [
                "VariationID", "GeneID", "GeneSymbol", "ClinicalSignificance",
                "PhenotypeList", "OriginSimple", "Assembly", "ReviewStatus",
                "NumberSubmitters", "RCVaccession", "AlleleID"
            ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(retained_variants)

    # 3. results/excluded_variants.csv
    excluded_file = output_dir / "excluded_variants.csv"
    with open(excluded_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["VariationID", "GeneID", "GeneSymbol", "ClinicalSignificance", "Reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(excluded_variants)

    # 4. results/summary.json
    summary_file = output_dir / "summary.json"
    top_genes_summary = ranking[:top_n]
    summary_content = {
        "analysis_metadata": {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": input_filename,
            "target_disease": "Cardiomyopathie hypertrophique (HCM/CMH)",
            "genome_assembly": "GRCh38",
            "allelic_origin": "germline",
            "top_n_requested": top_n,
        },
        "scientific_scope_note": (
            "Le champ ClinicalSignificance est une classification agregee au niveau "
            "du variant (VariationID) dans l'export variant_summary de ClinVar. "
            "Ces nombres representent des variants distincts repertories avec une classification "
            "pathogene ou probablement pathogene, et non une prevalence epidemiologique "
            "ou un decompte de patients atteints."
        ),
        "statistics": {
            "total_input_records": processed_data["total_records"],
            "total_retained_variants": total_retained,
            "total_excluded_records": processed_data["total_excluded"],
            "unique_genes_count": len(ranking),
            "accepted_classifications_breakdown": processed_data["accepted_significances"],
            "top_exclusion_reasons": processed_data["exclusion_reasons"],
        },
        "top_genes": top_genes_summary,
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_content, f, indent=2, ensure_ascii=False)

    # 5. results/top_genes.png
    plot_file = output_dir / "top_genes.png"
    generate_plot(ranking, top_n, total_retained, plot_file)

    return {
        "ranking_file": ranking_file,
        "variants_file": variants_file,
        "excluded_file": excluded_file,
        "summary_file": summary_file,
        "plot_file": plot_file,
    }


def generate_plot(ranking: list, top_n: int, total_retained: int, output_image_path: Path):
    """Génère un graphique à barres horizontales esthétique et lisible."""
    top_data = ranking[:top_n]
    if not top_data:
        # Cas limite si aucun variant retenu
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "Aucun variant pathogenic/likely pathogenic retenu", ha="center", va="center")
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=300)
        plt.close(fig)
        return

    # Inverser l'ordre pour afficher le gène n°1 tout en haut
    top_data_reversed = list(reversed(top_data))
    genes = [item["GeneSymbol"] for item in top_data_reversed]
    counts = [item["DistinctVariantCount"] for item in top_data_reversed]
    pcts = [item["PercentageOfRetainedVariants"] for item in top_data_reversed]

    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)

    # Palette de couleurs professionnelle
    colors = ["#1f77b4" if i < len(genes) - 2 else "#d62728" for i in range(len(genes))]
    # Les 2 premiers (en haut) mis en évidence (MYBPC3, MYH7)
    bars = ax.barh(genes, counts, color=colors, height=0.65, edgecolor="none", alpha=0.9)

    # Ajouter les étiquettes de valeur au bout des barres
    max_count = max(counts) if counts else 1
    for bar, count, pct in zip(bars, counts, pcts):
        width = bar.get_width()
        label_text = f" {count} ({pct:.1f}%)"
        ax.text(
            width + (max_count * 0.01),
            bar.get_y() + bar.get_height() / 2.0,
            label_text,
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#2c3e50"
        )

    # Ajustement des axes et du style
    ax.set_xlim(0, max_count * 1.15)
    ax.set_xlabel("Nombre de variants distincts (VariationID)", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_ylabel("Gène (symbole officiel HGNC)", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_title(
        f"Top {len(top_data)} des Gènes Associés à la Cardiomyopathie Hypertrophique dans ClinVar\n"
        f"Variants distincts 'Pathogenic' ou 'Likely pathogenic' (GRCh38, germline) — Total: {total_retained:,} variants",
        fontsize=12,
        fontweight="bold",
        pad=15
    )

    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")
    ax.tick_params(axis="both", which="major", labelsize=10)

    # Note de bas de page explicative
    fig.text(
        0.5, 0.01,
        "Source: NCBI ClinVar (variant_summary.txt.gz) — Décompte par VariationID distinct (non-prévalence clinique).",
        ha="center", fontsize=8, color="#666666", style="italic"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    plt.savefig(output_image_path, dpi=300)
    plt.close(fig)


def main():
    args = parse_arguments()
    try:
        results = process_dataset(args.variants)
        exported = export_results(results, args.output_dir, args.top, args.variants.name)

        print(f"[OK] Analyse terminee avec succes.")
        print(f"     Variants analyses : {results['total_records']}")
        print(f"     Variants retenus  : {results['total_retained']}")
        print(f"     Variants exclus   : {results['total_excluded']}")
        print(f"     Genes distincts   : {len(results['ranking'])}")
        print(f"     Fichiers generes  : {args.output_dir}/")
        for k, p in exported.items():
            print(f"       - {p.name}")
    except Exception as e:
        print(f"[ERREUR] Echec de l'analyse: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
