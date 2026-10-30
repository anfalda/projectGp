# Guide & Rapport Complet d'Intégration pour le Groupe

**Projet :** Analyse des variants génétiques de la cardiomyopathie hypertrophique dans ClinVar  
**Dépôt GitHub :** [https://github.com/ffmly/redesigned-spoon](https://github.com/ffmly/redesigned-spoon)  
**Date :** 30 Octobre 2026  
**Établissement :** Université Amar Telidji de Laghouat  
**Auteurs :** Équipe Projet (Étudiants 1 à 5)

---

## 1. Message Récapitulatif Prêt à Envoyer au Groupe (WhatsApp / Discord / Email)

> *« Salam l'équipe ! J'ai terminé l'intégration complète et la validation du projet selon le GUIDE_EQUIPE.md. Tout fonctionne à 100 % sans aucune erreur :*  
> *1. Le téléchargement, le contrôle SHA-256 et le filtrage Bash en flux streaming (17 027 lignes extraites).*  
> *2. L'analyse Python (scripts/analyze_genes.py) qui isole exactement 1 435 variants pathogènes sur 40 gènes, avec MYBPC3 (58,4 %) et MYH7 (21,5 %) en tête.*  
> *3. La suite de tests unitaires automatisés (tests/test_analyze_genes.py) avec 7 tests sur 7 validés.*  
> *4. Le rapport officiel de 4 pages (rapport.pdf) avec graphique haute résolution et tableau.*  
> *5. L'automatisation cron, les logs horodatés et l'archive tar.gz.*  
> *Le projet est propre, zippé et prêt à être soutenu devant le prof. Voici le compte-rendu complet pour que chacun maîtrise sa partie pour les questions de la soutenance ! »*

---

## 2. Répartition du Travail et Ce Qui a Été Réalisé par Rôle

### Étudiant 1 — Orchestration et Filtrage Shell
- **Fichiers gérés :** `run.sh`, `scripts/filter_hcm_variants.sh`, `LIEN_GIT.txt`.
- **Ce qui a été fait :**
  - Script d'orchestration POSIX strict `run.sh` avec `set -Eeuo pipefail`.
  - Gestion des options par `getopts` : `-c` (config), `-t` (Top N), `-f` (force download), `-n` (dry-run), `-h` (aide).
  - Gestion des signaux et pièges temporaires : `trap cleanup EXIT` et `trap on_signal INT TERM HUP` pour supprimer automatiquement les fichiers temporaires dans `tmp/`.
  - Filtre Shell en flux streaming `scripts/filter_hcm_variants.sh` sans décompression lourde sur disque : `gzip -cd | awk | sort | uniq`.
  - Sélection stricte : Assemblage `GRCh38`, origine `germline`, phénotype exact `Hypertrophic cardiomyopathy` (avec numéro facultatif).
  - Production du fichier intermédiaire `data/processed/hcm_variants_grch38.tsv` (17 027 lignes).
  - Archivage horodaté automatique sous `results/resultats_YYYYMMDD_HHMMSS.tar.gz`.

### Étudiant 2 — Source des Données et Intégrité Cryptographique
- **Fichiers gérés :** `SOURCES.md`, `config/dataset.env`.
- **Ce qui a été fait :**
  - Calcul et vérification de l'empreinte SHA-256 officielle sur le fichier de 456,5 Mo : `b235cd5742ac615d55703672751fa3ea71c8222d5ff0547cd1e9b107fd8a647f`.
  - Remplacement de la balise `TODO_ETUDIANT_2` dans `config/dataset.env`.
  - Rédaction exhaustive de `SOURCES.md` précisant la source (NCBI ClinVar), l'URL officielle, les conditions de réutilisation libre (domaine public US Government Work / CC0).
  - **Précision scientifique cruciale :** ClinVar `variant_summary` est un export agrégé au niveau du variant (`VariationID`). Le champ `ClinicalSignificance` est une classification synthétique et ne représente pas un décompte de patients ou une prévalence épidémiologique.

### Étudiant 3 — Algorithmique et Analyse Python
- **Fichiers gérés :** `scripts/analyze_genes.py`, `tests/test_analyze_genes.py`.
- **Ce qui a été fait :**
  - Implémentation du script `analyze_genes.py` avec `argparse` (`--variants`, `--output-dir`, `--top`).
  - Normalisation des classifications : acceptation stricte de `Pathogenic`, `Likely pathogenic`, `Pathogenic/Likely pathogenic`.
  - Exclusion tracée des VUS (7 930), bénins (5 714) et conflictuels (1 944) dans `results/excluded_variants.csv`.
  - Normalisation HGNC des symboles de gènes, rejet des symboles manquants (`-`, vide) et ambigus multi-gènes (présence de `;` due à des délétions chromosomiques).
  - Dédoublonnage strict par `VariationID` unique pour éviter de compter deux fois le même variant.
  - Calcul du classement décroissant et production de `results/gene_ranking.csv` et `results/summary.json`.
  - Génération de la figure graphique haute résolution (300 DPI) `results/top_genes.png` via Matplotlib.
  - Conception de la suite de tests automatisés `tests/test_analyze_genes.py` avec le framework standard `unittest` (7 tests unitaires indépendants validant 100 % de la logique).

### Étudiant 4 — Administration Système et Environnement
- **Fichiers gérés :** `requirements.txt`, `cron/clinvar_pipeline.cron`.
- **Ce qui a été fait :**
  - Déclaration minimale et propre des dépendances dans `requirements.txt` (`matplotlib>=3.8.0`).
  - Configuration de la tâche planifiée `cron/clinvar_pipeline.cron` avec exécution mensuelle le 1er du mois à 02h00 et rotation des journaux de plus de 90 jours.
  - Positionnement des droits d'exécution `chmod +x` sur tous les scripts.
  - Verrouillage en lecture seule des données brutes après téléchargement (`chmod a-w`).
  - Vérification de l'idempotence (le pipeline peut être relancé indéfiniment sans intervention manuelle).

### Étudiant 5 — Documentation et Validation Scientifique
- **Fichiers gérés :** `README.md`, `rapport.md`, `rapport.pdf`, `presentation.md`, `FICHE_VALIDATION_SUJET.md`.
- **Ce qui a été fait :**
  - Rédaction du `README.md` complet servant de manuel d'utilisation de référence.
  - Rédaction et compilation du rapport officiel de 4 pages `rapport.pdf` et `rapport.md`.
  - Préparation du support de soutenance `presentation.md` (10 diapositives avec notes de l'orateur).
  - Mise à jour de la fiche de cadrage `FICHE_VALIDATION_SUJET.md`.

---

## 3. Résultats Scientifiques Obtenus (Les Chiffres Clés à Retenir)

| Métrique | Valeur | Interprétation |
| :--- | :---: | :--- |
| **Lignes brutes filtrées (GRCh38, germline, HCM)** | **17 027** | Volume après le filtre Shell awk |
| **Variants exclus** | **15 592** | Dont 7 930 VUS, 5 714 bénins, 1 944 conflictuels |
| **Variants pathogènes retenus (P / LP)** | **1 435** | Ensemble final propre et dédoublonné |
| **Nombre de gènes distincts impliqués** | **40** | Tous documentés dans `results/gene_ranking.csv` |

### Le Top 10 des Gènes :
1. **MYBPC3** : **838 variants** (**58,40 %**) — Protéine sarcomérique C ; mutations tronquantes (haplo-insuffisance).
2. **MYH7** : **308 variants** (**21,46 %**) — Bêta-myosine cardiaque ; mutations faux-sens de la tête motrice.
   *(À eux deux, MYBPC3 et MYH7 totalisent 79,86 %, soit environ 80 % de toute la CMH).*
3. **FLNC** : **66 variants** (**4,60 %**) — Filamine C (cytosquelette / disque Z).
4. **TNNI3** : **56 variants** (**3,90 %**) — Troponine I cardiaque.
5. **TNNT2** : **32 variants** (**2,23 %**) — Troponine T2 cardiaque.
6. **TPM1** : **24 variants** (**1,67 %**) — Alpha-tropomyosine 1.
7. **TTN** : **15 variants** (**1,05 %**) — Titine.
8. **PRKAG2** : **11 variants** (**0,77 %**) — Phénocopie métabolique (syndrome de Wolff-Parkinson-White).
9. **MYL2** : **10 variants** (**0,70 %**) — Chaîne légère régulatrice.
10. **ALPK3** : **8 variants** (**0,56 %**) — Alpha-kinase 3.

---

## 4. Guide des Démonstrations pour la Soutenance (Questions Possibles du Prof)

### Question 1 : *« Montrez-moi que votre script run.sh respecte les exigences POSIX et de gestion d'erreur. »*
**Ce qu'il faut taper et expliquer :**
```bash
./run.sh -h
./run.sh -n
./run.sh -c fichier_inexistant.env
```
**Réponse orale :**  
*« Notre script `run.sh` utilise `set -Eeuo pipefail`. L'option `-h` affiche l'aide avec getopts, `-n` affiche le plan d'exécution sans toucher aux fichiers. Si on passe un fichier inexistant avec `-c`, le script l'intercepte immédiatement grâce à notre fonction `die()`, journalise l'erreur et retourne un code de sortie non nul (code 1), sans laisser de fichier temporaire grâce à notre fonction `cleanup()` branchée sur `trap EXIT`. »*

---

### Question 2 : *« Pourquoi avez-vous utilisé à la fois Bash et Python au lieu de tout faire en Python ? »*
**Réponse orale :**  
*« Le fichier brut ClinVar fait plus de 4 Go décompressé. Charger 4 Go en mémoire dans un script Python prendrait plusieurs gigaoctets de RAM et ralentirait l'exécution. En utilisant un filtre Shell en flux continu streaming (`gzip -cd | awk | sort | uniq`), nous n'extrayons que les lignes pertinentes sans jamais écrire les 4 Go sur disque. Cela réduit le fichier à 17 000 lignes (quelques mégaoctets). Ensuite, Python prend le relais là où il excelle : structures de données relationnelles, validation fine des symboles HGNC, statistiques, formatage JSON et génération de graphiques haute résolution avec Matplotlib. »*

---

### Question 3 : *« Comment prouvez-vous l'intégrité de vos données ? »*
**Ce qu'il faut montrer :**
Montrer la fonction `verify_file()` dans `run.sh` et le fichier `config/dataset.env`.
**Réponse orale :**  
*« Nous avons calculé l'empreinte SHA-256 officielle du fichier téléchargé (`b235cd57...`). Avant toute analyse, le script vérifie cette empreinte avec `sha256sum` et teste l'archive avec `gzip -t`. Dès que l'intégrité est validée, le fichier brut est protégé contre toute écriture accidentelle avec `chmod a-w`. »*

---

### Question 4 : *« Comment avez-vous testé votre code Python ? »*
**Ce qu'il faut taper :**
```bash
python3 -m unittest discover -s tests -v
```
**Réponse orale :**  
*« Nous avons écrit une suite de 7 tests unitaires dans `tests/test_analyze_genes.py` utilisant le framework standard `unittest`. Les tests utilisent un petit jeu de données synthétique indépendant de 8 variants. Ils vérifient que les variants pathogènes sont acceptés, que les bénins et VUS sont rejetés, qu'un même VariationID n'est compté qu'une seule fois, que les gènes manquants ou multi-gènes sont exclus, et que le classement final est parfaitement trié. Les 7 tests s'exécutent en 1,5 seconde. »*

---

### Question 5 : *« Quelle est la signification biologique de vos résultats ? »*
**Réponse orale :**  
*« Nos résultats montrent que 79,86 % des variants pathogènes de la cardiomyopathie hypertrophique se concentrent sur deux gènes sarcomériques : MYBPC3 (58,40 %) et MYH7 (21,46 %). Cela concorde parfaitement avec la littérature internationale (revue de Marian & Braunwald dans Circulation Research). MYBPC3 agit surtout par haplo-insuffisance via des mutations tronquantes, tandis que MYH7 agit par effet dominant-négatif au niveau de la tête motrice de la bêta-myosine. Nous observons également des gènes émergents du cytosquelette comme FLNC (4,60 %) et des phénocopies métaboliques comme PRKAG2 et LAMP2. »*

---

## 5. Fichiers et Livrables Inclus dans le Dossier

1. **`rapport.pdf`** : Le rapport académique officiel de 4 pages généré au format PDF avec mise en page soignée, tableau des résultats et figure haute résolution.
2. **`rapport.md`** : La version source Markdown du rapport.
3. **`presentation.md`** : Les 10 diapositives avec notes de présentation pour l'oral.
4. **`README.md`** : La documentation technique exhaustive du dépôt.
5. **`SOURCES.md`** : La documentation des sources de données et intégrité.
6. **`FICHE_VALIDATION_SUJET.md`** : Fiche de cadrage officielle de l'équipe.
7. **`LIEN_GIT.txt`** : Référence officielle du dépôt Git et commit final validé.
8. **`results/`** :
   - `gene_ranking.csv`
   - `variants_hcm.csv` (1 435 variants retenus)
   - `excluded_variants.csv` (15 592 variants exclus tracés)
   - `summary.json` (synthèse structurée)
   - `top_genes.png` (figure graphique 300 DPI)
   - `resultats_*.tar.gz` (archive datée des résultats)
9. **`cron/clinvar_pipeline.cron`** : Modèle de planification automatique.
10. **`requirements.txt`** : Dépendances Python (`matplotlib>=3.8.0`).
