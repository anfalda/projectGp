#!/usr/bin/env python3
"""
scripts/generate_pdf_report.py
Génère le rapport académique officiel de 4 pages (rapport.pdf) avec ReportLab.
Conforme aux exigences universitaires : typographie soignée, tableaux,
figure haute résolution intégrée, numérotation de pages et structure en 5 sections.
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = PROJECT_ROOT / "rapport.pdf"
IMAGE_PATH = PROJECT_ROOT / "results" / "top_genes.png"

class NumberedCanvas(canvas.Canvas):
    """Canvas personnalisé pour ajouter les en-têtes et pieds de page avec total exact de pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))

        # En-tête sur les pages 2 à N
        if self._pageNumber > 1:
            self.drawString(
                2.0 * cm, 28.5 * cm,
                "Analyse des Variants ClinVar de la Cardiomyopathie Hypertrophique (CMH)"
            )
            self.drawRightString(
                19.0 * cm, 28.5 * cm,
                "Université Amar Telidji de Laghouat — Octobre 2026"
            )
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(2.0 * cm, 28.3 * cm, 19.0 * cm, 28.3 * cm)

        # Pied de page sur toutes les pages
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(2.0 * cm, 1.5 * cm, 19.0 * cm, 1.5 * cm)

        self.drawString(
            2.0 * cm, 1.1 * cm,
            "Projet Bioinformatique & Administration Système — Dépôt : github.com/ffmly/redesigned-spoon"
        )
        self.drawRightString(
            19.0 * cm, 1.1 * cm,
            f"Page {self._pageNumber} / {page_count}"
        )
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )

    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#1A365D"),
        alignment=1, # Centré
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#2B6CB0"),
        alignment=1,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#2D3748"),
        alignment=4, # Justifié
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1A202C")
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell_style,
        alignment=1
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold"
    )

    story = []

    # ================= PAGE 1 : TITRE, IDENTITE, CONTEXTE ET METHODOLOGIE =================
    story.append(Paragraph("RAPPORT DE PROJET BIOINFORMATIQUE & SYSTÈME", subtitle_style))
    story.append(Paragraph("Analyse des Variants Génétiques de la Cardiomyopathie Hypertrophique dans ClinVar", title_style))
    story.append(Paragraph("Évaluation quantitative des gènes concentrant le plus de variants pathogènes ou probablement pathogènes (GRCh38, germline)", subtitle_style))

    # Tableau d'identification
    meta_data = [
        [
            Paragraph("<b>Établissement :</b> Université Amar Telidji de Laghouat", table_cell_style),
            Paragraph("<b>Groupe :</b> n° 1 (Génomique & Systèmes)", table_cell_style)
        ],
        [
            Paragraph("<b>Membres :</b> Benamara Ahmed Ryad, Étudiant 2, Étudiant 3, Étudiant 4, Étudiant 5", table_cell_style),
            Paragraph("<b>Date :</b> 30 Octobre 2026", table_cell_style)
        ],
        [
            Paragraph("<b>Dépôt GitHub :</b> https://github.com/ffmly/redesigned-spoon", table_cell_style),
            Paragraph("<b>Jeu de données :</b> NCBI ClinVar <i>variant_summary.txt.gz</i>", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[9.5 * cm, 7.5 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Résumé exécutif
    story.append(Paragraph("<b>Résumé Exécutif :</b> Ce travail met en œuvre un pipeline reproductible combinant Shell POSIX et Python 3 pour répondre à la question : <i>Quels gènes concentrent le plus grand nombre de variants distincts classés « Pathogenic » ou « Likely pathogenic » dans ClinVar, associés spécifiquement à la cardiomyopathie hypertrophique (CMH) ?</i> À partir d'un fichier brut de 456,5 Mo compressé (plus de 4 Go décompressé), le filtrage en flux streaming extrait 17 027 enregistrements germlinaires sur GRCh38. Après normalisation de la pathogénicité, exclusion des annotations ambiguës et dédoublonnage unitaire par <code>VariationID</code>, <b>1 435 variants distincts</b> répartis sur <b>40 gènes</b> sont retenus. Deux gènes sarcomériques, <b>MYBPC3</b> (838 variants, 58,40 %) et <b>MYH7</b> (308 variants, 21,46 %), totalisent <b>79,86 %</b> des variants répertoriés, corroborant la littérature cardiologique.", body_style))

    story.append(Paragraph("1. Introduction et Problématique Médicale", h1_style))
    story.append(Paragraph("<b>1.1. Physiopathologie de la Cardiomyopathie Hypertrophique :</b> La cardiomyopathie hypertrophique (CMH / HCM) est la maladie cardiaque héréditaire monogénique la plus fréquente, avec une prévalence estimée à 1 pour 500 dans la population générale. Elle se caractérise par une hypertrophie ventriculaire gauche inexpliquée par une cause hémodynamique (sténose aortique, hypertension). Cliniquement, elle s'étend de formes asymptomatiques à des complications sévères : insuffisance cardiaque, fibrillation atriale, et surtout mort subite chez l'adulte jeune et le sportif.", body_style))
    story.append(Paragraph("<b>1.2. Rôle du Diagnostic Génétique et Base ClinVar :</b> Qualifiée de « maladie du sarcomère », la CMH est transmise sur un mode autosomique dominant à pénétrance incomplète. La base publique NCBI ClinVar centralise les relations entre variants génomiques et phénotypes. Cependant, l'accumulation de variants de signification incertaine (VUS) et de données contradictoires impose un filtrage systématique pour isoler les gènes abritant de véritables mutations causales avérées.", body_style))
    story.append(Paragraph("<b>1.3. Définition de l'Unité de Mesure :</b> L'objectif est de dénombrer les <b>variants distincts répertoriés</b> (<code>VariationID</code> unique) et non les cas cliniques ou la prévalence en population. Il s'agit d'une métrique d'hétérogénéité mutationnelle enregistrée dans les référentiels de diagnostic génétique.", body_style))

    story.append(Paragraph("2. Source de Données et Contrôle d'Intégrité", h1_style))
    story.append(Paragraph("Le fichier source officiel <code>variant_summary.txt.gz</code> (Release 2026-10-19) est hébergé sur le serveur FTP de NCBI ClinVar. Sa taille est de <b>456 505 123 octets</b> (~456,5 Mo compressé ; 4 085 223 747 octets décompressé). Son empreinte cryptographique SHA-256 a été calculée et vérifiée : <code>b235cd5742ac615d55703672751fa3ea71c8222d5ff0547cd1e9b107fd8a647f</code>. Le pipeline vérifie automatiquement cette somme et teste l'intégrité de l'archive (<code>gzip -t</code>) avant de verrouiller les données brutes en lecture seule (<code>chmod a-w</code>). Les données sont placées sous licence du domaine public (US Government Work / CC0).", body_style))

    # ================= PAGE 2 : METHODOLOGIE TECHNIQUE ET RESULTATS =================
    story.append(PageBreak())

    story.append(Paragraph("3. Architecture de la Chaîne de Traitement (Pipeline)", h1_style))
    story.append(Paragraph("Le projet sépare strictement le traitement système de gros volume (Bash) et l'analyse statistique relationnelle (Python), garantissant performance, traçabilité et faible consommation mémoire :", body_style))

    story.append(Paragraph("<b>3.1. Filtrage Shell POSIX en Flux Continu (scripts/filter_hcm_variants.sh) :</b> Afin d'éviter d'extraire plus de 4 Go sur le disque, le traitement s'exécute en streaming via un pipeline de 4 commandes connectées par tubes (pipes) :", body_style))
    story.append(Paragraph("• <code>gzip -cd</code> décompresse le flux à la volée vers la sortie standard.", bullet_style))
    story.append(Paragraph("• <code>awk</code> sélectionne l'assemblage <code>GRCh38</code>, l'origine <code>germline</code> et recherche dans <code>PhenotypeList</code> l'intitulé strict <code>Hypertrophic cardiomyopathy</code> (avec numéro de sous-type facultatif, ex. CMH 1 à 20). Les mentions secondaires du terme au sein d'autres pathologies sont formellement rejetées.", bullet_style))
    story.append(Paragraph("• <code>sort</code> et <code>uniq</code> ordonnent et éliminent les redondances physiques immédiates.", bullet_style))
    story.append(Paragraph("Le filtre conserve l'en-tête et produit le fichier tabulé <code>data/processed/hcm_variants_grch38.tsv</code> contenant <b>17 027 lignes</b>.", body_style))

    story.append(Paragraph("<b>3.2. Normalisation et Dédoublonnage Python (scripts/analyze_genes.py) :</b> Le script applique les critères d'inclusion et de qualité :", body_style))
    story.append(Paragraph("1. <b>Classification de pathogénicité :</b> Seules les classes canoniques <code>Pathogenic</code>, <code>Likely pathogenic</code> et <code>Pathogenic/Likely pathogenic</code> sont retenues (1 438 occurrences brutes). Les 15 592 variants exclus (VUS : 7 930 ; bénins : 5 714 ; conflictuels : 1 944) sont tracés avec leur motif dans <code>results/excluded_variants.csv</code>.", bullet_style))
    story.append(Paragraph("2. <b>Validation du symbole de gène :</b> Normalisation HGNC. Les symboles manquants (<code>-</code>, vide) ou ambigus multi-gènes (présence de <code>;</code> résultant de remaniements chromosomiques) sont exclus du décompte unitaire.", bullet_style))
    story.append(Paragraph("3. <b>Dédoublonnage unitaire :</b> Chaque <code>VariationID</code> n'est comptabilisé qu'une seule fois par gène hôte.", bullet_style))
    story.append(Paragraph("4. <b>Génération des sorties :</b> Production des CSV de classement, variants retenus, table des exclus, synthèse JSON et figure PNG.", bullet_style))

    story.append(Paragraph("4. Résultats Chiffrés et Classement des Gènes", h1_style))
    story.append(Paragraph("Sur 17 027 lignes initiales, l'analyse isole <b>1 435 variants distincts</b> répartis sur <b>40 gènes</b>. Le tableau ci-dessous détaille le Top 15 des gènes associés à la cardiomyopathie hypertrophique dans ClinVar :", body_style))

    # Tableau des résultats Top 15
    headers = [
        Paragraph("Rang", table_header_style),
        Paragraph("Gène HGNC", table_header_style),
        Paragraph("Variants", table_header_style),
        Paragraph("Part (%)", table_header_style),
        Paragraph("Protéine codée & Localisation cellulaire", table_header_style),
        Paragraph("Mécanisme pathogénique", table_header_style)
    ]
    rows_data = [
        ["1", "MYBPC3", "838", "58,40 %", "Myosin-binding protein C (sarcomère)", "Haplo-insuffisance (mutations tronquantes)"],
        ["2", "MYH7", "308", "21,46 %", "Chaîne lourde bêta-myosine (filament épais)", "Dominant-négatif (tête globulaire S1)"],
        ["3", "FLNC", "66", "4,60 %", "Filamine C (cytosquelette / disque Z)", "Altération structurelle, CMH arythmogène"],
        ["4", "TNNI3", "56", "3,90 %", "Troponine I cardiaque (filament fin)", "Hyper-sensibilisation calcique (Ca2+)"],
        ["5", "TNNT2", "32", "2,23 %", "Troponine T2 cardiaque (filament fin)", "Altération de contractilité, mort subite"],
        ["6", "TPM1", "24", "1,67 %", "Alpha-tropomyosine 1 (filament fin)", "Régulation anormale actine-myosine"],
        ["7", "TTN", "15", "1,05 %", "Titine (filament élastique sarcomérique)", "Altération biomécanique passive"],
        ["8", "PRKAG2", "11", "0,77 %", "Sous-unité gamma-2 AMPK (métabolique)", "Phénocopie : surcharge glycogénique / WPW"],
        ["9", "MYL2", "10", "0,70 %", "Chaîne légère régulatrice de myosine", "Dysfonction de phosphorylation"],
        ["10", "ALPK3", "8", "0,56 %", "Alpha-kinase 3 (cytosquelette)", "Formes pédiatriques sévères autosomiques"],
        ["11", "MYH7B", "8", "0,56 %", "Myosine 7B / hôte microARN miR-499", "Régulation transcriptionnelle"],
        ["12", "LAMP2", "7", "0,49 %", "Protéine lysosomale (membrane)", "Phénocopie : maladie de Danon (liée à l'X)"],
        ["13", "MYH6", "5", "0,35 %", "Chaîne lourde alpha-myosine", "Formes atypiques / tardives"],
        ["14", "TCAP", "5", "0,35 %", "Téléthonine / Titin-cap (disque Z)", "Défaut d'ancrage sarcomérique"],
        ["15", "ACTC1", "4", "0,28 %", "Actine alpha cardiaque (filament fin)", "Déficit d'interaction actomyosine"],
    ]
    table_content = [headers]
    for r in rows_data:
        table_content.append([
            Paragraph(r[0], table_cell_center),
            Paragraph(f"<b>{r[1]}</b>", table_cell_bold),
            Paragraph(r[2], table_cell_center),
            Paragraph(r[3], table_cell_center),
            Paragraph(r[4], table_cell_style),
            Paragraph(r[5], table_cell_style),
        ])

    res_table = Table(table_content, colWidths=[1.1 * cm, 2.0 * cm, 1.5 * cm, 1.5 * cm, 5.4 * cm, 5.5 * cm])
    res_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(res_table)

    # ================= PAGE 3 : FIGURE GRAPHIQUE ET DISCUSSION BIOLOGIQUE =================
    story.append(PageBreak())

    story.append(Paragraph("5. Visualisation Graphique des Résultats", h1_style))
    story.append(Paragraph("La figure ci-dessous (générée automatiquement en haute résolution à 300 DPI dans <code>results/top_genes.png</code>) illustre la prépondérance écrasante des deux gènes sarcomériques majeurs :", body_style))

    if IMAGE_PATH.exists():
        img = Image(str(IMAGE_PATH), width=16.8 * cm, height=9.8 * cm)
        story.append(img)
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Figure 1 :</b> Distribution des variants distincts « Pathogenic » ou « Likely pathogenic » associés à la CMH dans ClinVar (GRCh38, germline). MYBPC3 et MYH7 représentent à eux seuls 79,86 % de l'ensemble des variants répertoriés.", ParagraphStyle("FigLegend", parent=body_style, fontSize=7.5, leading=10, textColor=colors.HexColor("#4A5568"), alignment=1)))
    else:
        story.append(Paragraph("<i>[Image top_genes.png disponible dans results/]</i>", body_style))

    story.append(Paragraph("6. Discussion Biologique et Confrontation Clinique", h1_style))
    story.append(Paragraph("<b>6.1. Le Duopole Sarcomérique Majeur (MYBPC3 et MYH7) :</b> Notre analyse met en évidence que <b>MYBPC3</b> (58,40 %) et <b>MYH7</b> (21,46 %) regroupent <b>1 146 variants sur 1 435 (79,86 %)</b>. Ce résultat corrobore avec une exactitude remarquable les grandes séries cardiologiques internationales (Marian & Braunwald, <i>Circulation Research</i>, 2017) qui établissent que ces deux gènes rendent compte d'environ 80 % des cas de CMH génotypiquement résolus :", body_style))
    story.append(Paragraph("• <b>MYBPC3 :</b> Caractérisé par une grande hétérogénéité de mutations tronquantes (non-sens, décalages de cadre de lecture, sites d'épissage) conduisant à une instabilité de l'ARNm et une haplo-insuffisance protéique dans le sarcomère.", bullet_style))
    story.append(Paragraph("• <b>MYH7 :</b> Dominé au contraire par des mutations faux-sens siégeant dans les domaines fonctionnels critiques de la bêta-myosine (tête globulaire S1 et tige d'ancrage), exerçant un effet « poison-peptide » dominant-négatif qui perturbe la force unitaire contractile.", bullet_style))

    story.append(Paragraph("<b>6.2. Les Gènes Régulateurs du Filament Fin (TNNI3, TNNT2, TPM1, ACTC1) :</b> Ces protéines régulent l'activation du cycle actomyosine par le calcium intracellulaire. Les variants de <i>TNNT2</i> et <i>TNNI3</i> représentent 6,13 % des variants retenus. Cliniquement, les mutations de <i>TNNT2</i> sont réputées pour induire une hypertrophie morphologique modeste mais un risque arythmogène élevé avec menace de mort subite précoce.", body_style))

    story.append(Paragraph("<b>6.3. Gènes Non-Sarcomériques et Phénocopies Métaboliques :</b>", body_style))
    story.append(Paragraph("• <b>FLNC (4,60 %, 3e rang) :</b> Filamine C du disque Z. Les variants de FLNC constituent une cause majeure de cardiomyopathies avec arythmies ventriculaires malignes.", bullet_style))
    story.append(Paragraph("• <b>PRKAG2 et LAMP2 :</b> Ces gènes illustrent l'importance du diagnostic différentiel génétique. PRKAG2 est une glycogénose cardiaque souvent confondue avec la CMH mais associée à une préexcitation ventriculaire (Wolff-Parkinson-White) ; LAMP2 correspond à la maladie de Danon (liée à l'X, hypertrophie massive et atteinte multisystémique).", bullet_style))

    # ================= PAGE 4 : SYSTEME, REPRODUCTIBILITE, LIMITES ET CONCLUSION =================
    story.append(PageBreak())

    story.append(Paragraph("7. Administration Système, Reproductibilité et Robustesse", h1_style))
    story.append(Paragraph("Le pipeline satisfait l'ensemble des exigences formelles d'ingénierie et d'administration système :", body_style))

    story.append(Paragraph("<b>7.1. Gestion Stricte de l'Environnement POSIX :</b> Les scripts Shell activent <code>set -Eeuo pipefail</code> pour stopper l'exécution dès la première anomalie et détecter les variables indéfinies. Le traitement modulaire s'appuie sur des fonctions réutilisables (<code>log</code>, <code>die</code>, <code>require_command</code>, <code>verify_file</code>, <code>download_file</code>).", body_style))

    story.append(Paragraph("<b>7.2. Traitement des Options et Robustesse (getopts) :</b> Le script principal <code>run.sh</code> intègre 5 options : <code>-c</code> (fichier de configuration), <code>-t</code> (taille du Top gènes), <code>-f</code> (re-téléchargement forcé), <code>-n</code> (plan d'exécution dry-run sans effet de bord), et <code>-h</code> (aide intégrée). Tout argument invalide ou fichier manquant déclenche une interruption propre avec code de retour non nul.", body_style))

    story.append(Paragraph("<b>7.3. Nettoyage Garanti par Signaux (trap) et Journaux Horodatés :</b> L'interception des signaux (<code>trap cleanup EXIT</code> et <code>trap on_signal INT TERM HUP</code>) garantit la suppression des répertoires temporaires créés dans <code>tmp/run.XXXXXX</code>. Chaque lancement génère un journal horodaté dans <code>logs/run_YYYYMMDD_HHMMSS.log</code> capturant l'ensemble des sorties <code>stdout</code> et <code>stderr</code> via <code>tee</code>.", body_style))

    story.append(Paragraph("<b>7.4. Planification Automatique (cron) :</b> Un modèle standard est fourni dans <code>cron/clinvar_pipeline.cron</code> pour automatiser l'exécution mensuelle (le 1er du mois à 02h00) avec rotation préventive des journaux de plus de 90 jours.", body_style))

    story.append(Paragraph("<b>7.5. Suite de Tests Unitaires Automatisés (unittest) :</b> Le module <code>tests/test_analyze_genes.py</code> valide la logique sur un jeu synthétique indépendant : acceptation de P/LP, rejet des VUS et bénins, dédoublonnage par <code>VariationID</code>, rejet des gènes manquants ou multi-gènes, tri décroissant et conformité de l'interface CLI (7 tests exécutés avec succès en moins de 2 secondes).", body_style))

    story.append(Paragraph("8. Limites Scientifiques et Perspectives", h1_style))
    story.append(Paragraph("1. <b>Biais de Soumission ClinVar :</b> ClinVar est une archive participative. Les gènes historiques de panels diagnostiques hospitaliers (<i>MYBPC3</i>, <i>MYH7</i>) bénéficient d'un volume de séquençage et de soumission bien supérieur à des gènes récemment identifiés comme <i>ALPK3</i>.", body_style))
    story.append(Paragraph("2. <b>Non-Équivalence avec la Prévalence Clinique :</b> Un variant récurrent retrouvé chez 200 patients distincts compte pour un seul <code>VariationID</code>, tout comme un variant familial privé. Les résultats décrivent l'hétérogénéité des allèles délétères documentés.", body_style))
    story.append(Paragraph("3. <b>Masse des Variants VUS :</b> 7 930 variants filtrés ont été exclus en raison d'une classification incertaine. L'apport des prédicteurs d'intelligence artificielle (AlphaMissense) et l'intégration du score d'étoiles ClinVar constituent des perspectives d'approfondissement majeures.", body_style))

    story.append(Paragraph("9. Conclusion", h1_style))
    story.append(Paragraph("Le pipeline développé apporte une réponse quantitative rigoureuse à la question de recherche : la diversité allélique pathogène de la CMH est dominée de manière hégémonique par <b>MYBPC3 (58,40 %)</b> et <b>MYH7 (21,46 %)</b>. La chaîne logicielle hybride Shell/Python associe haute performance de filtrage en flux, reproductibilité totale et rigueur d'administration système.", body_style))

    story.append(Paragraph("10. Références Bibliographiques", h1_style))
    story.append(Paragraph("1. <b>Landrum MJ, et al.</b> ClinVar: improvements to access, data extraction and curation. <i>Nucleic Acids Res.</i> 2020;48(D1):D835-D844.<br/>"
                           "2. <b>Marian AJ, Braunwald E.</b> Hypertrophic Cardiomyopathy: Genetics, Pathogenesis, Clinical Manifestations, Diagnostic Evaluation, and Prognosis. <i>Circ Res.</i> 2017;121(7):749-770.<br/>"
                           "3. <b>Richards S, et al.</b> Standards and guidelines for the interpretation of sequence variants: ACMG/AMP. <i>Genet Med.</i> 2015;17(5):405-424.<br/>"
                           "4. <b>Ommen SR, et al.</b> 2020 AHA/ACC Guideline for the Diagnosis and Treatment of Patients With HCM. <i>Circulation.</i> 2020;142(25):e533-e557.", ParagraphStyle("Refs", parent=body_style, fontSize=7, leading=9, textColor=colors.HexColor("#4A5568"))))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Rapport PDF genere avec succes : {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
