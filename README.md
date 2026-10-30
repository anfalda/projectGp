# Analyse des Variants Génétiques de la Cardiomyopathie Hypertrophique dans ClinVar

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Bash 5.0+](https://img.shields.io/badge/bash-5.0+-green.svg)](https://www.gnu.org/software/bash/)
[![Dataset ClinVar](https://img.shields.io/badge/data-NCBI%20ClinVar-orange.svg)](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz)
[![License: CC0 / Public Domain](https://img.shields.io/badge/license-Public%20Domain-lightgrey.svg)](SOURCES.md)

Ce projet implémente un pipeline bioinformatique automatisé et reproductible combinant **Bash** et **Python 3** pour identifier et hiérarchiser les gènes concentrant le plus grand nombre de variants distincts classés **« Pathogenic »** ou **« Likely pathogenic »** dans la base de données **NCBI ClinVar**, spécifiquement associés à la **cardiomyopathie hypertrophique (CMH / HCM)**.

---

## Sommaire

1. [Problématique Scientifique et Objet d'Étude](#1-problématique-scientifique-et-objet-détude)
2. [Architecture du Projet](#2-architecture-du-projet)
3. [Chaîne de Traitement (Pipeline)](#3-chaîne-de-traitement-pipeline)
4. [Prérequis et Installation](#4-prérequis-et-installation)
5. [Guide d'Exécution](#5-guide-dexécution)
   - [Exécution complète avec run.sh](#exécution-complète-avec-runsh)
   - [Options de ligne de commande (getopts)](#options-de-ligne-de-commande-getopts)
   - [Exécution modulaire (Filtre Shell & Analyse Python)](#exécution-modulaire-filtre-shell--analyse-python)
6. [Tests Automatiques](#6-tests-automatiques)
7. [Fichiers de Résultats et Interprétation Biologique](#7-fichiers-de-résultats-et-interprétation-biologique)
   - [Classement des principaux gènes](#classement-des-principaux-gènes)
   - [Description des sorties](#description-des-sorties)
8. [Administration Système et Reproductibilité](#8-administration-système-et-reproductibilité)
9. [Dépannage et FAQ](#9-dépannage-et-faq)

---

## 1. Problématique Scientifique et Objet d'Étude

- **Question de recherche :** *Quels gènes concentrent le plus de variants distincts classés « Pathogenic » ou « Likely pathogenic » dans ClinVar, associés spécifiquement à la cardiomyopathie hypertrophique ?*
- **Pathologie étudiée :** La **cardiomyopathie hypertrophique (CMH)** est une maladie myocardique génétique fréquente (prévalence estimée à 1/500 dans la population générale), caractérisée par une hypertrophie ventriculaire gauche inexpliquée par une surcharge de pression ou de volume. Elle constitue l'une des causes majeures de mort subite chez l'adulte jeune et l'athlète.
- **Distinction scientifique essentielle :** L'analyse porte sur le nombre de **variants distincts répertoriés** (`VariationID` unique dans ClinVar) et non sur la prévalence clinique ou le nombre de patients porteurs. Le résultat décrit l'hétérogénéité mutationnelle documentée dans les bases de données d'interprétation clinique.

---

## 2. Architecture du Projet

```text
redesigned-spoon/
│
├── config/
│   └── dataset.env              # Variables d'environnement, URLs officielles et SHA-256
│
├── cron/
│   └── clinvar_pipeline.cron     # Configuration d'automatisation planifiée cron
│
├── data/
│   ├── raw/                     # Données brutes téléchargées (variant_summary.txt.gz)
│   └── processed/               # Données filtrées intermédiaires (hcm_variants_grch38.tsv)
│
├── logs/                        # Fichiers journaux horodatés (run_YYYYMMDD_HHMMSS.log)
│
├── results/                     # Résultats finaux d'analyse
│   ├── gene_ranking.csv         # Classement des gènes par nombre de variants
│   ├── variants_hcm.csv         # Table des variants pathogènes retenus
│   ├── excluded_variants.csv    # Table des enregistrements exclus et motifs
│   ├── summary.json             # Synthèse statistique et métadonnées
│   ├── top_genes.png            # Graphique haute résolution du Top gènes
│   └── resultats_*.tar.gz       # Archive horodatée des résultats
│
├── scripts/
│   ├── filter_hcm_variants.sh   # Étape Shell : décompression en flux et filtrage strict
│   └── analyze_genes.py         # Étape Python : dédoublonnage, calculs et visualisations
│
├── tests/
│   └── test_analyze_genes.py    # Suite de tests unitaires automatisés (unittest)
│
├── tmp/                         # Fichiers temporaires nettoyés par trap EXIT
├── run.sh                       # Script d'orchestration principal (POSIX Bash)
├── requirements.txt             # Dépendances logicielles Python
├── README.md                    # Documentation complète du projet
├── SOURCES.md                   # Fiche descriptive des sources de données et intégrité
├── FICHE_VALIDATION_SUJET.md    # Fiche de cadrage académique
├── GUIDE_EQUIPE.md              # Guide d'organisation et interfaces d'équipe
└── LIEN_GIT.txt                 # Lien vers le dépôt GitHub et identifiant de commit
```

---

## 3. Chaîne de Traitement (Pipeline)

Le projet applique une séparation claire des responsabilités entre **Bash** (flux système, gestion de fichiers, filtrage de gros volumes) et **Python** (normalisation, structures relationnelles, statistiques et visualisation graphique) :

```
[NCBI ClinVar] -> variant_summary.txt.gz (~456.5 Mo compressé, ~4.1 Go décompressé)
       │
       ▼ (1. Téléchargement & Contrôle d'intégrité)
  curl / sha256sum / gzip -t
       │
       ▼ (2. Filtrage Shell haute performance en flux)
  scripts/filter_hcm_variants.sh
  - Assemblage : GRCh38
  - Origine : germline
  - Phénotype : Hypertrophic cardiomyopathy (strict)
       │
       ▼
  data/processed/hcm_variants_grch38.tsv (17 027 lignes)
       │
       ▼ (3. Analyse Python, dédoublonnage et tri)
  scripts/analyze_genes.py
  - Retient : Pathogenic, Likely pathogenic, Pathogenic/Likely pathogenic
  - Exclut : VUS, Benign, Conflicting, gènes manquants ou multi-gènes (;)
  - Dédoublonne par VariationID unitaire
       │
       ▼ (4. Génération des résultats)
  results/gene_ranking.csv, variants_hcm.csv, excluded_variants.csv, summary.json, top_genes.png
       │
       ▼ (5. Archivage horodaté & Nettoyage)
  results/resultats_YYYYMMDD_HHMMSS.tar.gz & trap cleanup
```

---

## 4. Prérequis et Installation

### Système d'exploitation
- **Linux** (Debian, Ubuntu, RHEL, Arch) ou **WSL 2** (Windows Subsystem for Linux avec Ubuntu).
- Également compatible avec l'environnement **Git Bash** sous Windows.

### Outils système requis
- `bash` (version >= 4.4)
- `curl` (téléchargement réseau)
- `gzip` (compression/décompression)
- `awk`, `sort`, `uniq`, `tar`, `tee`, `mktemp`
- `sha256sum` ou `shasum`

### Environnement Python
- Python 3.10 ou version supérieure.
- Installation des dépendances via pip :

```bash
pip install -r requirements.txt
```

---

## 5. Guide d'Exécution

### Rendre les scripts exécutables
Avant la première utilisation, assurez-vous que les permissions d'exécution sont positionnées :
```bash
chmod +x run.sh scripts/filter_hcm_variants.sh scripts/analyze_genes.py tests/test_analyze_genes.py
```

### Exécution complète avec `run.sh`
Pour exécuter l'ensemble de la chaîne de bout en bout (téléchargement conditionnel, filtrage, analyse Python, archivage et logs) :

```bash
./run.sh
```

### Options de ligne de commande (`getopts`)
Le script `run.sh` intègre plusieurs options documentées :

| Option | Argument | Description | Valeur par défaut |
| :--- | :--- | :--- | :--- |
| `-c` | `FILE` | Chemin vers un fichier de configuration alternatif | `config/dataset.env` |
| `-t` | `N` | Nombre de gènes affichés dans la figure finale | `15` |
| `-f` | Aucun | Force le re-téléchargement même si le fichier brut existe | Désactivé |
| `-n` | Aucun | Mode *dry-run* : affiche le plan d'exécution sans traitement | Désactivé |
| `-h` | Aucun | Affiche l'aide détaillée et quitte | — |

**Exemples :**
```bash
# Afficher l'aide
./run.sh -h

# Afficher le plan d'exécution sans toucher aux données
./run.sh -n

# Exécuter avec un Top 20 de gènes
./run.sh -t 20

# Forcer le re-téléchargement de la base ClinVar
./run.sh -f
```

### Exécution modulaire (Filtre Shell & Analyse Python)

Si vous souhaitez exécuter séparément chaque composant :

```bash
# 1. Étape Shell seule
./scripts/filter_hcm_variants.sh data/raw/variant_summary.txt.gz data/processed/hcm_variants_grch38.tsv

# 2. Étape Python seule
python3 scripts/analyze_genes.py \
  --variants data/processed/hcm_variants_grch38.tsv \
  --output-dir results \
  --top 15
```

---

## 6. Tests Automatiques

Une suite de tests unitaires complète basée sur le module standard `unittest` de Python est fournie dans `tests/test_analyze_genes.py`. Elle vérifie sur des jeux de données synthétiques indépendants :
1. L'acceptation stricte des classes `Pathogenic`, `Likely pathogenic` et `Pathogenic/Likely pathogenic`.
2. Le rejet des classifications bénignes, incertaines (VUS) et conflictuelles.
3. Le dédoublonnage des `VariationID` identiques pour un même gène.
4. L'exclusion documentée des symboles de gènes manquants (`-`, vide, `NA`).
5. L'exclusion documentée des symboles de gènes ambigus multi-gènes (séparateur `;`).
6. Le tri décroissant exact du classement des gènes.
7. La conformité de l'interface CLI et la création des 5 livrables.

Pour lancer les tests :
```bash
python3 -m unittest discover -s tests -v
```

---

## 7. Fichiers de Résultats et Interprétation Biologique

### Classement des principaux gènes

Sur le jeu de données officiel ClinVar (Release 2026-10-19, 17 027 lignes HCM brutes dans GRCh38), après filtrage strict et dédoublonnage, **1 435 variants distincts** répartis sur **40 gènes** sont retenus :

| Rang | Symbole Gène | Nom de la Protéine | Variants Distincts | Part (%) | Rôle Physiopathologique |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **MYBPC3** | Myosin-binding protein C, cardiaque | **838** | **58,40 %** | Protéine sarcomérique clé ; mutations tronquantes fréquentes (haplo-insuffisance). |
| **2** | **MYH7** | Chaîne lourde de bêta-myosine cardiaque | **308** | **21,46 %** | Protéine du filament épais ; mutations faux-sens dominantes au niveau de la tête motrice. |
| **3** | **FLNC** | Filamine C | **66** | **4,60 %** | Protéine du disque Z et du cytosquelette intercalaire ; associée aux formes arythmogènes. |
| **4** | **TNNI3** | Troponine I cardiaque | **56** | **3,90 %** | Composante du complexe régulateur de la troponine du filament fin. |
| **5** | **TNNT2** | Troponine T2 cardiaque | **32** | **2,23 %** | Régulation calcique de la contraction ; associée à des risques de mort subite précoce. |
| **6** | **TPM1** | Tropomyosine 1 (alpha) | **24** | **1,67 %** | Filament fin du sarcomère. |
| **7** | **TTN** | Titine | **15** | **1,05 %** | Protéine géante de cohésion élastique du sarcomère. |
| **8** | **PRKAG2** | Sous-unité gamma-2 de la protéine kinase AMPK | **11** | **0,77 %** | Phénocopie métabolique de CMH avec préexcitation ventriculaire (WPW). |
| **9** | **MYL2** | Chaîne légère régulatrice de myosine | **10** | **0,70 %** | Filament épais. |
| **10** | **ALPK3** | Alpha-kinase 3 | **8** | **0,56 %** | Régulateur de l'intégrité sarcomérique (formes néonatales/sévères). |

> **Constat biologique majeur :** Les gènes sarcomériques classiques **MYBPC3** et **MYH7** concentrent à eux seuls **79,86 % (~80 %)** de l'ensemble des variants pathogènes recensés, confirmant pleinement les données établies de la littérature médicale internationale (Marian & Braunwald, 2017).

### Description des sorties

- **`results/gene_ranking.csv`** : Tableau récapitulatif classé contenant le rang, le symbole HGNC, le décompte de variants et le pourcentage.
- **`results/variants_hcm.csv`** : Tableau complet de l'ensemble des 1 435 variants retenus avec leurs identifiants ClinVar (`VariationID`, `AlleleID`, `RCVaccession`, etc.).
- **`results/excluded_variants.csv`** : Traçabilité intégrale des 15 592 variants exclus avec le motif précis (classification non retenue, gène ambigu, doublon).
- **`results/summary.json`** : Fichier JSON structuré pour intégration web ou programmatique contenant les métadonnées, statistiques globales et note de portée scientifique.
- **`results/top_genes.png`** : Graphique haute résolution (300 DPI) à barres horizontales prêt pour l'intégration dans le rapport scientifique.
- **`results/resultats_YYYYMMDD_HHMMSS.tar.gz`** : Archive compressée d'intégrité regroupant les 5 fichiers de résultats générés lors de l'exécution.

---

## 8. Administration Système et Reproductibilité

1. **Intégrité cryptographique (SHA-256) :**  
   Avant tout traitement, `run.sh` vérifie l'empreinte SHA-256 du jeu de données brut téléchargé pour éviter toute corruption de données ou attaque par rejeu.
2. **Nettoyage automatique par signaux (`trap`) :**  
   Le script configure `trap cleanup EXIT` et `trap on_signal INT TERM HUP`. Tout fichier temporaire dans `tmp/` est supprimé proprement en cas de succès ou d'interruption par `Ctrl+C`.
3. **Protection des données brutes en lecture seule :**  
   Dès son téléchargement et sa vérification, le fichier `data/raw/variant_summary.txt.gz` est verrouillé en lecture seule via `chmod a-w`.
4. **Journaux d'exécution horodatés :**  
   Chaque exécution génère un fichier journal dédié `logs/run_YYYYMMDD_HHMMSS.log` capturant la sortie standard et d'erreur avec horodatage millimétré.
5. **Répétabilité sans intervention manuelle :**  
   Le pipeline peut être relancé indéfiniment de manière idempotente sans nettoyage préalable.
6. **Planification automatique (Cron) :**  
   Le fichier `cron/clinvar_pipeline.cron` permet de déployer une exécution mensuelle automatique pour intégrer les mises à jour publiées par NCBI ClinVar.

---

## 9. Dépannage et FAQ

- **Erreur `Interpreteur Python introuvable` :**  
  Spécifiez explicitement le binaire Python via la variable `PYTHON_BIN` :  
  `PYTHON_BIN=/usr/bin/python3 ./run.sh`
- **Erreur `Somme SHA-256 incorrecte` :**  
  Vérifiez que le téléchargement n'a pas été tronqué. Utilisez l'option `-f` pour forcer un re-téléchargement complet :  
  `./run.sh -f`
- **Exécution sous Windows / Git Bash :**  
  Le script utilise des commandes POSIX standards (`awk`, `gzip`, `curl`). Sous Windows, utilisez Git Bash ou WSL Ubuntu pour une compatibilité parfaite.

---

## Membres de l'Équipe et Contributions

- **Étudiant 1 :** Orchestration générale (`run.sh`), filtre Shell (`scripts/filter_hcm_variants.sh`), intégration globale.
- **Étudiant 2 :** Analyse des sources, documentation `SOURCES.md`, intégrité SHA-256 et configuration `config/dataset.env`.
- **Étudiant 3 :** Développement du script Python d'analyse `scripts/analyze_genes.py` et suite de tests `tests/test_analyze_genes.py`.
- **Étudiant 4 :** Environnement, gestion des dépendances `requirements.txt`, automatisation `cron/clinvar_pipeline.cron` et permissions système.
- **Étudiant 5 :** Documentation `README.md`, rapport scientifique `rapport.md`, support de présentation `presentation.md` et fiche de validation.
