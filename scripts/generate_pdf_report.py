#!/usr/bin/env python3
"""
scripts/generate_pdf_report.py
Genere rapport.pdf (4 pages) a partir des VRAIS resultats du pipeline :
results/summary.json, results/gene_ranking.csv, results/top_genes.png
et config/dataset.env. Aucun chiffre de resultat n'est ecrit a la main :
relancer ./run.sh puis ce script met le rapport a jour automatiquement.

Usage : python3 scripts/generate_pdf_report.py
"""
import csv
import json
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = ROOT / "rapport.pdf"
RESULTS = ROOT / "results"
IMAGE_PATH = RESULTS / "top_genes.png"
LOGO_PATH = ROOT / "assets" / "usthb_logo.png"
REPO_URL = "https://github.com/anfalda/projectGp"

MEMBERS = [
    ("AGGOUN SOUNDOUS YASMINE", "222231369119"),
    ("DAOUDI ANFAL", "232331601003"),
    ("TOUBAL ABDELGHANI", "202131068318"),
    ("ZAOURAR MERIEM", "222231355920"),
    ("BELFERKOUS IMENE", "212231693910"),
]

# Proprietes du fichier fige (copie mensuelle archivee de ClinVar)
SIZE_GZ = "450\u00a0727\u00a0547"
SIZE_RAW = "4\u00a0043\u00a0056\u00a0609"

GENE_INFO = {  # symbole -> (proteine, mecanisme)
    "MYBPC3": ("Myosin-binding protein C (sarcomère)", "Haplo-insuffisance (mutations tronquantes)"),
    "MYH7": ("Chaîne lourde bêta-myosine (filament épais)", "Dominant-négatif (tête globulaire S1)"),
    "FLNC": ("Filamine C (cytosquelette / disque Z)", "Altération structurelle, CMH arythmogène"),
    "TNNI3": ("Troponine I cardiaque (filament fin)", "Hyper-sensibilisation calcique (Ca2+)"),
    "TNNT2": ("Troponine T2 cardiaque (filament fin)", "Altération de contractilité, mort subite"),
    "TPM1": ("Alpha-tropomyosine 1 (filament fin)", "Régulation anormale actine-myosine"),
    "TTN": ("Titine (filament élastique sarcomérique)", "Altération biomécanique passive"),
    "PRKAG2": ("Sous-unité gamma-2 AMPK (métabolique)", "Phénocopie : surcharge glycogénique / WPW"),
    "MYL2": ("Chaîne légère régulatrice de myosine", "Dysfonction de phosphorylation"),
    "MYL3": ("Chaîne légère essentielle de myosine", "Altération du filament épais"),
    "ALPK3": ("Alpha-kinase 3 (cytosquelette)", "Formes pédiatriques sévères autosomiques"),
    "MYH7B": ("Myosine 7B / hôte microARN miR-499", "Régulation transcriptionnelle"),
    "LAMP2": ("Protéine lysosomale (membrane)", "Phénocopie : maladie de Danon (liée à l'X)"),
    "MYH6": ("Chaîne lourde alpha-myosine", "Formes atypiques / tardives"),
    "TCAP": ("Téléthonine / Titin-cap (disque Z)", "Défaut d'ancrage sarcomérique"),
    "ACTC1": ("Actine alpha cardiaque (filament fin)", "Déficit d'interaction actomyosine"),
    "JPH2": ("Jonctophiline-2 (jonction membrane / réticulum)", "Altération du couplage excitation-contraction"),
    "CSRP3": ("Protéine LIM musculaire (disque Z)", "Défaut de mécanosensibilité"),
    "PLN": ("Phospholamban (réticulum sarcoplasmique)", "Altération de la recapture du calcium"),
}


# ---------------------------------------------------------------- utilitaires
def fr_int(n):
    return f"{int(n):,}".replace(",", "\u00a0")


def fr_pct(x, d=2):
    return f"{x:.{d}f}".replace(".", ",") + "\u00a0%"


def code(t):
    return f'<font face="Courier" size="7.6">{t}</font>'


def read_env():
    env = {}
    p = ROOT / "config" / "dataset.env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*([A-Z_0-9]+)="?([^"#]*)"?', line)
            if m:
                env[m.group(1)] = m.group(2).strip()
    return env


def load_results():
    sj, gr = RESULTS / "summary.json", RESULTS / "gene_ranking.csv"
    if not sj.exists() or not gr.exists():
        sys.exit("results/summary.json ou results/gene_ranking.csv introuvable : lancez d'abord ./run.sh")
    stats = json.loads(sj.read_text(encoding="utf-8"))["statistics"]
    genes = []
    with open(gr, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            genes.append((int(r["Rank"]), r["GeneSymbol"], int(r["DistinctVariantCount"])))
    return stats, genes


class NumberedCanvas(canvas.Canvas):
    """En-tetes et pieds de page avec le nombre total de pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.decorate(n)
            super().showPage()
        super().save()

    def decorate(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        if self._pageNumber > 1:
            self.drawString(2.0 * cm, 28.5 * cm, "Analyse des Variants ClinVar de la Cardiomyopathie Hypertrophique (CMH)")
            self.drawRightString(19.0 * cm, 28.5 * cm, "USTHB — Faculté d'Informatique — 2026/2027")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(2.0 * cm, 28.3 * cm, 19.0 * cm, 28.3 * cm)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(2.0 * cm, 1.5 * cm, 19.0 * cm, 1.5 * cm)
        self.drawString(2.0 * cm, 1.1 * cm, "Projet Programmation Script — Dépôt : github.com/anfalda/projectGp")
        self.drawRightString(19.0 * cm, 1.1 * cm, f"Page {self._pageNumber} / {page_count}")
        self.restoreState()


# ---------------------------------------------------------------- rapport
def build_pdf():
    stats, genes = load_results()
    env = read_env()
    release = env.get("CLINVAR_RELEASE", "2026-10")
    filename = env.get("VARIANT_FILENAME", "variant_summary_2026-10.txt.gz")
    sha = env.get("VARIANT_SHA256", "")

    n_in = stats["total_input_records"]
    n_kept = stats["total_retained_variants"]
    n_excl = stats["total_excluded_records"]
    n_genes = stats["unique_genes_count"]
    reasons = stats["top_exclusion_reasons"]
    uncertain = sum(v for k, v in reasons.items() if "Uncertain" in k)
    benign = sum(v for k, v in reasons.items() if "benign" in k.lower())
    conflict = sum(v for k, v in reasons.items() if "Conflicting" in k)
    other = n_excl - uncertain - benign - conflict
    raw_plp = n_in - sum(v for k, v in reasons.items() if k.startswith("Classification non retenue"))

    cnt = {g: c for _, g, c in genes}
    pct = lambda c: c / n_kept * 100
    top15 = genes[:15]
    n1, n2 = cnt.get("MYBPC3", 0), cnt.get("MYH7", 0)
    duo = n1 + n2
    thin2 = cnt.get("TNNT2", 0) + cnt.get("TNNI3", 0)

    doc = SimpleDocTemplate(str(OUTPUT_PDF), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.7 * cm, bottomMargin=1.8 * cm,
                            title="Rapport - Variants ClinVar de la cardiomyopathie hypertrophique",
                            author="Groupe n° 1")
    ss = getSampleStyleSheet()
    ink = colors.HexColor("#2D3748")
    navy = colors.HexColor("#1A365D")
    body = ParagraphStyle("Body", parent=ss["Normal"], fontName="Helvetica", fontSize=9, leading=12.3,
                          textColor=ink, alignment=4, spaceAfter=4.5)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, firstLineIndent=-8, spaceAfter=2.5)
    body_left = ParagraphStyle("BodyLeft", parent=body, alignment=0)
    h1 = ParagraphStyle("H1", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=11.5, leading=14,
                        textColor=navy, spaceBefore=8, spaceAfter=3, keepWithNext=True)
    cell = ParagraphStyle("Cell", parent=ss["Normal"], fontName="Helvetica", fontSize=8, leading=10,
                          textColor=colors.HexColor("#1A202C"))
    cell_c = ParagraphStyle("CellC", parent=cell, alignment=1)
    cell_b = ParagraphStyle("CellB", parent=cell, fontName="Helvetica-Bold")
    head = ParagraphStyle("Head", parent=cell, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)
    center = lambda size, bold=False, color=ink, lead=None: ParagraphStyle(
        "C%s%s" % (size, bold), parent=ss["Normal"], fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size, leading=lead or size * 1.25, textColor=color, alignment=1)

    story = []

    # ---------- bloc d'identification (page de garde compacte) ----------
    logo = ""
    if LOGO_PATH.exists():
        lw, lh = ImageReader(str(LOGO_PATH)).getSize()
        logo = Image(str(LOGO_PATH), width=2.0 * cm, height=2.0 * cm * lh / lw)
    uni = [
        Paragraph("Université des Sciences et de la Technologie Houari Boumediene (USTHB)", center(10, True, navy)),
        Paragraph("Faculté d'Informatique — Département IA &amp; SD — Spécialité : BIOINFORMATIQUE", center(8.5)),
        Spacer(1, 3),
        Paragraph("RAPPORT DE PROJET — SYSTÈME DE PROGRAMMATION SCRIPT", center(11.5, True, navy)),
        Paragraph("Année universitaire 2026/2027 · Groupe n° 1", center(8.5)),
    ]
    idt = Table([[logo, uni]], colWidths=[2.6 * cm, 14.8 * cm])
    idt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    story.append(idt)
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Thème : Quels gènes concentrent le plus de variants distincts classés « Pathogenic » ou « Likely pathogenic » "
        "dans ClinVar, associés spécifiquement à la cardiomyopathie hypertrophique ?", center(11, True, navy, 14)))
    story.append(Spacer(1, 5))
    rows = [[Paragraph("NOM ET PRÉNOM", head), Paragraph("MATRICULE", head)]]
    for name, mat in MEMBERS:
        rows.append([Paragraph(name, cell), Paragraph(mat, cell_c)])
    mt = Table(rows, colWidths=[10.4 * cm, 4.6 * cm], hAlign="CENTER")
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    story.append(mt)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        f"Dépôt GitHub : {REPO_URL} · Jeu de données : NCBI ClinVar <i>{filename}</i> (release {release}) · "
        "Rapport généré automatiquement à partir des résultats du pipeline.", center(7.5, False, colors.HexColor("#555555"))))

    # ---------- Resume ----------
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "<b>Résumé :</b> ce travail met en œuvre un pipeline reproductible combinant Shell POSIX et Python 3 pour "
        "répondre à la question : <i>quels gènes concentrent le plus grand nombre de variants distincts classés "
        "« Pathogenic » ou « Likely pathogenic » dans ClinVar, associés spécifiquement à la cardiomyopathie "
        f"hypertrophique (CMH) ?</i> À partir d'un fichier de 450,7 Mo compressé "
        f"(plus de 4 Go décompressé), le filtrage en flux extrait <b>{fr_int(n_in)}</b> enregistrements germinaux sur GRCh38. "
        f"Après normalisation de la pathogénicité, exclusion des annotations ambiguës et dédoublonnage par {code('VariationID')}, "
        f"<b>{fr_int(n_kept)} variants distincts</b> répartis sur <b>{n_genes} gènes</b> sont retenus. "
        f"<b>MYBPC3</b> ({fr_int(n1)} variants, {fr_pct(pct(n1))}) et <b>MYH7</b> ({fr_int(n2)}, {fr_pct(pct(n2))}) "
        f"totalisent <b>{fr_pct(pct(duo))}</b> des variants répertoriés, en cohérence avec la littérature cardiologique.", body))

    # ---------- 1 ----------
    story.append(Paragraph("1. Introduction et Problématique Médicale", h1))
    story.append(Paragraph(
        "<b>1.1. Physiopathologie :</b> la cardiomyopathie hypertrophique (CMH / HCM) est la maladie cardiaque héréditaire "
        "monogénique la plus fréquente, avec une prévalence estimée à 1 pour 500 dans la population générale. Elle se "
        "caractérise par une hypertrophie ventriculaire gauche inexpliquée par une cause hémodynamique (sténose aortique, "
        "hypertension). Cliniquement, elle s'étend de formes asymptomatiques à des complications sévères : insuffisance "
        "cardiaque, fibrillation atriale et surtout mort subite chez l'adulte jeune et le sportif.", body))
    story.append(Paragraph(
        "<b>1.2. Diagnostic génétique et ClinVar :</b> qualifiée de « maladie du sarcomère », la CMH est transmise sur un "
        "mode autosomique dominant à pénétrance incomplète. La base publique NCBI ClinVar centralise les relations entre "
        "variants génomiques et phénotypes. L'accumulation de variants de signification incertaine (VUS) et de données "
        "contradictoires impose un filtrage systématique pour isoler les gènes abritant de véritables variants pathogènes.", body))
    story.append(Paragraph(
        f"<b>1.3. Unité de mesure :</b> on dénombre les <b>variants distincts répertoriés</b> ({code('VariationID')} unique) et "
        "non les cas cliniques ou la prévalence en population. Il s'agit d'une métrique d'hétérogénéité mutationnelle "
        "enregistrée dans les référentiels de diagnostic génétique.", body))

    # ---------- 2 ----------
    story.append(Paragraph("2. Source de Données et Contrôle d'Intégrité", h1))
    story.append(Paragraph(
        f"Le fichier utilisé est {code(filename)}, copie mensuelle <b>archivée</b> (release {release}) de l'export public "
        f"{code('variant_summary.txt.gz')} de NCBI ClinVar. Contrairement au fichier « courant », qui est remplacé "
        "régulièrement, cette copie ne change pas : sa somme SHA-256 reste valide et les résultats sont identiques sur toute "
        f"machine. Taille : <b>{SIZE_GZ} octets</b> (~450,7 Mo compressé ; {SIZE_RAW} octets décompressé). "
        f"SHA-256 : {code(sha)}. Le pipeline vérifie automatiquement cette somme et teste l'archive ({code('gzip -t')}) avant de "
        f"verrouiller les données brutes en lecture seule ({code('chmod a-w')}). Les données sont mises à disposition par le "
        "NCBI sans restriction d'utilisation (voir SOURCES.md).", body_left))

    # ---------- 3 ----------
    story.append(Paragraph("3. Architecture de la Chaîne de Traitement et Définition du Motif", h1))
    story.append(Paragraph(
        "Le projet sépare le traitement système de gros volume (Bash) et l'analyse statistique (Python), ce qui garantit "
        "performance, traçabilité et faible consommation mémoire.", body))
    story.append(Paragraph(
        f"<b>Motif recherché :</b> variant ClinVar d'assemblage {code('GRCh38')}, d'origine {code('germline')}, dont la liste "
        f"{code('PhenotypeList')} contient exactement l'intitulé « Hypertrophic cardiomyopathy » (numéro de sous-type "
        f"facultatif), classé {code('Pathogenic')}, {code('Likely pathogenic')} ou {code('Pathogenic/Likely pathogenic')}, "
        f"et compté une seule fois par {code('VariationID')}.", body))
    story.append(Paragraph(
        f"<b>3.1. Filtrage Shell en flux ({code('scripts/filter_hcm_variants.sh')}) :</b> pour éviter d'extraire plus de "
        "4 Go sur le disque, le traitement s'exécute en streaming par un enchaînement de 4 commandes reliées par des tubes :", body))
    story.append(Paragraph(f"• {code('gzip -cd')} décompresse le flux à la volée vers la sortie standard.", bullet))
    story.append(Paragraph(
        f"• {code('awk')} garde l'assemblage GRCh38, l'origine germline et un élément de {code('PhenotypeList')} égal à "
        "« Hypertrophic cardiomyopathy » (avec numéro de sous-type facultatif). Une simple mention du terme dans une autre "
        "pathologie est rejetée.", bullet))
    story.append(Paragraph(f"• {code('sort')} et {code('uniq')} ordonnent et éliminent les doublons exacts.", bullet))
    story.append(Paragraph(
        f"Le filtre conserve l'en-tête et produit {code('data/processed/hcm_variants_grch38.tsv')} : <b>{fr_int(n_in)} lignes</b>.", body))
    story.append(Paragraph(
        f"<b>3.2. Normalisation et dédoublonnage Python ({code('scripts/analyze_genes.py')}) :</b>", body))
    story.append(Paragraph(
        f"1. <b>Classification :</b> seules les classes {code('Pathogenic')}, {code('Likely pathogenic')} et "
        f"{code('Pathogenic/Likely pathogenic')} sont retenues ({fr_int(raw_plp)} occurrences brutes). Les "
        f"<b>{fr_int(n_excl)}</b> enregistrements exclus (VUS : {fr_int(uncertain)} ; bénins : {fr_int(benign)} ; "
        f"conflictuels : {fr_int(conflict)} ; autres : {fr_int(other)}) sont tracés avec leur motif dans "
        f"{code('results/excluded_variants.csv')}.", bullet))
    story.append(Paragraph(
        f"2. <b>Symbole de gène :</b> les symboles manquants ({code('-')}, vide) ou ambigus (variants multi-gènes séparés "
        f"par {code(';')}) sont exclus du décompte.", bullet))
    story.append(Paragraph(
        f"3. <b>Dédoublonnage :</b> chaque {code('VariationID')} n'est compté qu'une seule fois.", bullet))
    story.append(Paragraph(
        "4. <b>Sorties :</b> CSV de classement, variants retenus, exclus, synthèse JSON et figure PNG.", bullet))

    # ---------- 4 ----------
    story.append(Paragraph("4. Résultats Chiffrés et Classement des Gènes", h1))
    story.append(Paragraph(
        f"Sur {fr_int(n_in)} lignes initiales, l'analyse retient <b>{fr_int(n_kept)} variants distincts</b> répartis sur "
        f"<b>{n_genes} gènes</b> ({fr_pct(n_kept / n_in * 100)} des lignes). Top 15 des gènes :", body))
    data = [[Paragraph(t, head) for t in ["Rang", "Gène HGNC", "Variants", "Part (%)", "Protéine codée", "Mécanisme pathogénique"]]]
    for rank, g, c in top15:
        prot, mech = GENE_INFO.get(g, ("—", "—"))
        data.append([Paragraph(str(rank), cell_c), Paragraph(g, cell_b), Paragraph(fr_int(c), cell_c),
                     Paragraph(fr_pct(pct(c)), cell_c), Paragraph(prot, cell), Paragraph(mech, cell)])
    rt = Table(data, colWidths=[1.1 * cm, 2.0 * cm, 1.5 * cm, 1.5 * cm, 5.5 * cm, 5.8 * cm], repeatRows=1)
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    story.append(rt)

    # ---------- 5 ----------
    story.append(Paragraph("5. Visualisation Graphique des Résultats", h1))
    story.append(Paragraph(
        f"La figure ci-dessous est produite automatiquement par le pipeline ({code('results/top_genes.png')}) :", body))
    if IMAGE_PATH.exists():
        iw, ih = ImageReader(str(IMAGE_PATH)).getSize()
        w = 16.0 * cm
        story.append(Image(str(IMAGE_PATH), width=w, height=w * ih / iw))
        story.append(Paragraph(
            "<b>Figure 1 :</b> variants distincts « Pathogenic » ou « Likely pathogenic » associés à la CMH dans ClinVar "
            f"(GRCh38, germline). MYBPC3 et MYH7 représentent {fr_pct(pct(duo))} des variants retenus.",
            ParagraphStyle("Fig", parent=body, fontSize=7.5, leading=10, alignment=1, textColor=colors.HexColor("#4A5568"))))
    else:
        story.append(Paragraph("<i>[Figure results/top_genes.png introuvable : lancez ./run.sh]</i>", body))

    # ---------- 6 ----------
    story.append(Paragraph("6. Discussion Biologique", h1))
    story.append(Paragraph(
        f"<b>6.1. Le duo MYBPC3 / MYH7 :</b> MYBPC3 ({fr_pct(pct(n1))}) et MYH7 ({fr_pct(pct(n2))}) regroupent "
        f"<b>{fr_int(duo)} variants sur {fr_int(n_kept)} ({fr_pct(pct(duo))})</b>. Ce résultat est cohérent avec la revue de "
        "Marian et Braunwald (<i>Circulation Research</i>, 2017), qui désigne ces deux gènes comme les plus fréquemment "
        "impliqués chez les patients génotypés ; notre analyse compte toutefois des variants et non des patients.", body))
    story.append(Paragraph(
        "• <b>MYBPC3 :</b> grande hétérogénéité de variants tronquants (non-sens, décalages du cadre de lecture, sites "
        "d'épissage) conduisant à une haplo-insuffisance protéique.", bullet))
    story.append(Paragraph(
        "• <b>MYH7 :</b> surtout des variants faux-sens dans la tête motrice de la bêta-myosine, avec un effet "
        "dominant-négatif sur la force contractile.", bullet))
    story.append(Paragraph(
        f"<b>6.2. Filament fin (TNNI3, TNNT2, TPM1, ACTC1) :</b> ces protéines régulent le cycle actomyosine par le calcium. "
        f"TNNT2 et TNNI3 représentent {fr_pct(pct(thin2))} des variants retenus ; les variants de TNNT2 sont réputés "
        "associés à une hypertrophie modeste mais à un risque arythmogène élevé.", body))
    story.append(Paragraph(
        f"<b>6.3. Gènes non sarcomériques et phénocopies :</b> FLNC ({fr_pct(pct(cnt.get('FLNC', 0)))}, 3e rang) code la "
        "filamine C du disque Z et est associé à des cardiomyopathies avec arythmies ventriculaires. PRKAG2 "
        "(glycogénose cardiaque avec préexcitation de type Wolff-Parkinson-White) et LAMP2 (maladie de Danon, liée à l'X) "
        "illustrent l'importance du diagnostic différentiel génétique.", body))

    # ---------- 7 ----------
    story.append(Paragraph("7. Administration Système, Reproductibilité et Robustesse", h1))
    story.append(Paragraph(
        f"<b>7.1. Script strict :</b> {code('set -Eeuo pipefail')} stoppe l'exécution à la première anomalie. Les fonctions "
        f"réutilisables sont {code('log')}, {code('die')}, {code('require_command')}, {code('verify_file')} et "
        f"{code('download_file')}.", body))
    story.append(Paragraph(
        f"<b>7.2. Options ({code('getopts')}) :</b> {code('run.sh')} accepte {code('-c')} (configuration), {code('-t')} "
        f"(taille du Top), {code('-f')} (re-téléchargement), {code('-n')} (plan sans effet) et {code('-h')} (aide). "
        "Un argument invalide ou un fichier manquant provoque un arrêt propre avec un code de retour non nul.", body))
    story.append(Paragraph(
        f"<b>7.3. Signaux et journaux :</b> {code('trap cleanup EXIT')} et {code('trap on_signal INT TERM HUP')} suppriment "
        f"le dossier temporaire {code('tmp/run.XXXXXX')} et le téléchargement inachevé. Chaque lancement écrit un journal "
        f"horodaté {code('logs/run_YYYYMMDD_HHMMSS.log')} via {code('tee')}.", body))
    story.append(Paragraph(
        f"<b>7.4. Planification :</b> {code('cron/clinvar_pipeline.cron')} lance le pipeline chaque mois (le 1er à 02h00) "
        "et supprime les journaux de plus de 90 jours.", body))
    story.append(Paragraph(
        f"<b>7.5. Tests :</b> {code('tests/test_analyze_genes.py')} ({code('unittest')}) vérifie sur un jeu synthétique les "
        "classes acceptées et rejetées, les symboles de gènes, le dédoublonnage, le tri, l'interface en ligne de commande "
        "et la création des 5 fichiers de résultats (7 tests).", body))

    # ---------- 8 ----------
    story.append(Paragraph("8. Limites Scientifiques et Perspectives", h1))
    story.append(Paragraph(
        "1. <b>Biais de soumission :</b> ClinVar est une base participative ; les gènes des panels diagnostiques historiques "
        "(MYBPC3, MYH7) y sont davantage soumis que des gènes récents comme ALPK3.", bullet))
    story.append(Paragraph(
        f"2. <b>Variants et non patients :</b> un variant porté par 200 patients compte pour un seul {code('VariationID')}, "
        "comme un variant privé observé dans une seule famille. Les résultats ne sont pas une prévalence.", bullet))
    story.append(Paragraph(
        f"3. <b>Incertitude :</b> {fr_int(uncertain)} enregistrements de signification incertaine (VUS) et {fr_int(conflict)} "
        "classifications conflictuelles sont exclus ; leur reclassement futur pourrait modifier le classement. Les "
        "prédicteurs d'intelligence artificielle (AlphaMissense) et le niveau de relecture ClinVar sont des perspectives.", bullet))

    # ---------- 9 ----------
    story.append(Paragraph("9. Conclusion", h1))
    story.append(Paragraph(
        f"Le pipeline répond à la question posée : la diversité des variants pathogènes de la CMH dans ClinVar est dominée "
        f"par <b>MYBPC3 ({fr_pct(pct(n1))})</b> et <b>MYH7 ({fr_pct(pct(n2))})</b>. La chaîne Shell / Python associe filtrage "
        "en flux, reproductibilité (fichier figé et somme de contrôle) et rigueur d'administration système.", body))

    # ---------- 10 ----------
    story.append(Paragraph("10. Références Bibliographiques", h1))
    story.append(Paragraph(
        "1. <b>Landrum MJ, et al.</b> ClinVar: improvements to access, data extraction and curation. <i>Nucleic Acids Res.</i> 2020;48(D1):D835-D844.<br/>"
        "2. <b>Marian AJ, Braunwald E.</b> Hypertrophic Cardiomyopathy: Genetics, Pathogenesis, Clinical Manifestations, Diagnostic Evaluation, and Prognosis. <i>Circ Res.</i> 2017;121(7):749-770.<br/>"
        "3. <b>Richards S, et al.</b> Standards and guidelines for the interpretation of sequence variants: ACMG/AMP. <i>Genet Med.</i> 2015;17(5):405-424.<br/>"
        "4. <b>Ommen SR, et al.</b> 2020 AHA/ACC Guideline for the Diagnosis and Treatment of Patients With HCM. <i>Circulation.</i> 2020;142(25):e533-e557.",
        ParagraphStyle("Refs", parent=body, fontSize=7, leading=9, alignment=0, textColor=colors.HexColor("#4A5568"))))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Rapport PDF genere : {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
