# Support de Présentation : Soutenance de Projet

## Analyse des Variants Génétiques de la Cardiomyopathie Hypertrophique dans ClinVar

---

### Slide 1 : Titre et Identification du Projet
- **Sujet :** Quels gènes concentrent le plus de variants distincts classés « Pathogenic » ou « Likely pathogenic » dans ClinVar, associés spécifiquement à la cardiomyopathie hypertrophique ?
- **Pathologie :** Cardiomyopathie hypertrophique (CMH / HCM)
- **Équipe :** 5 étudiants (Orchestration, Données, Python, Système, Documentation)
- **Dépôt GitHub :** `https://github.com/ffmly/redesigned-spoon`

*Notes du présentateur :*  
Bienvenue à tous. Aujourd'hui, nous vous présentons notre projet d'ingénierie bioinformatique et d'administration système portant sur l'analyse génétique de la cardiomyopathie hypertrophique dans la base mondiale NCBI ClinVar.

---

### Slide 2 : Problématique Médicale et Biologique
- **La CMH :** Maladie myocardique héréditaire la plus fréquente (1/500 personnes).
- **Conséquences :** Hypertrophie anormale du ventricule gauche, risque majeur de mort subite chez les jeunes.
- **Enjeu génétique :** Maladie du sarcomère à transmission autosomique dominante.
- **Question clé :** Quels sont les gènes clés de la maladie recensés dans les banques de données cliniques actuelles ?
- **Précision méthodologique :** Nous dénombrons les **variants distincts répertoriés** (`VariationID` ClinVar) et non la prévalence épidémiologique en population générale.

*Notes du présentateur :*  
La cardiomyopathie hypertrophique est causée par des mutations touchant l'appareil contractile cardiaque. Notre objectif n'est pas de compter les patients hospitalisés, mais de cartographier la diversité allélique documentée dans ClinVar.

---

### Slide 3 : Architecture et Chaîne de Traitement Globale
- **Données brutes :** NCBI ClinVar `variant_summary.txt.gz` (456,5 Mo compressé, ~4,1 Go décompressé).
- **Étape 1 :** Téléchargement, vérification d'intégrité SHA-256 et verrouillage en lecture seule.
- **Étape 2 :** Filtrage en flux continu streaming par **Shell POSIX** (GRCh38, germline, libellé HCM exact).
- **Étape 3 :** Normalisation, dédoublonnage et calcul du classement par **Python 3**.
- **Étape 4 :** Génération automatique de 5 sorties (CSV, JSON, PNG) et archivage `.tar.gz`.

*Notes du présentateur :*  
Nous avons articulé le travail en combinant la puissance de Bash pour le traitement en flux des 4 Go de données, et la flexibilité de Python pour les calculs statistiques et la visualisation.

---

### Slide 4 : Filtrage Shell POSIX (scripts/filter_hcm_variants.sh)
- **Traitement en flux streaming sans décompression intégrale sur disque :**
  ```bash
  gzip -cd input.gz | awk ... | sort ... | uniq > output.tsv
  ```
- **Critères appliqués :**
  - Assemblage : `Assembly == "GRCh38"`
  - Origine allélique : `OriginSimple == "germline"`
  - Phénotype strict : `Hypertrophic cardiomyopathy` (avec numéro de sous-type facultatif, ex. CMH 1)
- **Résultat intermédiaire :** 17 027 lignes extraites avec en-tête conservé dans `data/processed/hcm_variants_grch38.tsv`.

*Notes du présentateur :*  
Ce filtre élimine les faux positifs tels que les maladies mitochondriales qui mentionnent incidemment le terme hypertrophie. Plus de trois commandes sont enchaînées par des tubes UNIX pour une efficacité maximale.

---

### Slide 5 : Analyse et Algorithmique Python (scripts/analyze_genes.py)
- **1. Normalisation de la pathogénicité :**
  - Retenus : `Pathogenic`, `Likely pathogenic`, `Pathogenic/Likely pathogenic`
  - Rejetés : VUS (7 930), Bénins (4 894), Conflictuels (1 944)
- **2. Validation du symbole de gène :**
  - Rejet des gènes manquants (`-`, vide) et ambigus multi-gènes (présence de `;`)
- **3. Dédoublonnage par VariationID :**
  - Chaque `VariationID` unique n'est comptabilisé qu'une seule fois par gène.
- **4. Sorties normalisées :** CSV de classement, variants retenus, table des exclus, JSON et figure PNG.

*Notes du présentateur :*  
Chaque étape de décision est documentée et transparente. Plus de 15 000 variants non retenus sont tracés avec leur motif d'exclusion exact dans `results/excluded_variants.csv`.

---

### Slide 6 : Résultats Clés — Le Palmarès des Gènes
- **Total analysé :** 17 027 enregistrements
- **Variants pathogènes retenus :** **1 435 variants distincts** répartis sur **40 gènes**
- **Top 5 des gènes :**
  1. **MYBPC3** : **838 variants** (**58,40 %**)
  2. **MYH7** : **308 variants** (**21,46 %**)
  3. **FLNC** : **66 variants** (**4,60 %**)
  4. **TNNI3** : **56 variants** (**3,90 %**)
  5. **TNNT2** : **32 variants** (**2,23 %**)

*Notes du présentateur :*  
Voici le résultat central de notre étude : deux gènes sarcomériques, MYBPC3 et MYH7, concentrent à eux seuls près de 80 % de tous les variants pathogènes connus pour la cardiomyopathie hypertrophique.

---

### Slide 7 : Interprétation Biologique et Médicale
- **MYBPC3 (58,4 %) :** Mutations de perte de fonction (tronquantes, décalages de lecture) agissant par **haplo-insuffisance**.
- **MYH7 (21,5 %) :** Mutations faux-sens de la tête motrice de la bêta-myosine agissant par mécanisme **dominant-négatif**.
- **FLNC (4,6 %) :** Filamine C du cytosquelette, impliquée dans les formes restrictives et arythmogènes sévères.
- **Troponines (TNNI3, TNNT2, TPM1) :** Régulation fine du calcium sarcomérique.

*Notes du présentateur :*  
Ces résultats empiriques issus de ClinVar s'alignent parfaitement avec les grandes séries cliniques publiées dans la littérature internationale, notamment par Marian et Braunwald.

---

### Slide 8 : Administration Système et Reproductibilité
- **POSIX & Bash strict :** `set -Eeuo pipefail`
- **Intégrité cryptographique :** Somme SHA-256 validée avant tout traitement.
- **Gestion des signaux :** `trap cleanup EXIT` et `trap on_signal INT TERM HUP` pour nettoyer `tmp/`.
- **Protection des données :** `chmod a-w` sur le fichier brut.
- **Automatisation planifiée :** Script cron dans `cron/clinvar_pipeline.cron` (rafraîchissement mensuel).
- **Journaux horodatés :** `logs/run_YYYYMMDD_HHMMSS.log` complets pour audit.

*Notes du présentateur :*  
Le pipeline est 100 % reproductible et idempotent. Il peut être relancé indéfiniment sans aucune intervention manuelle ni corruption de fichier temporaire.

---

### Slide 9 : Tests Automatisés (tests/test_analyze_genes.py)
- Framework standard Python : `unittest`
- Jeu synthétique indépendant de 8 variants représentatifs (rapide et portable) :
  - Validation des classes pathogènes acceptées
  - Rejet des bénins et des VUS
  - Dédoublonnage d'un même `VariationID`
  - Rejet des gènes manquants et des multi-gènes
  - Vérification du tri décroissant et de la génération des fichiers
- Exécution en une commande : `python3 -m unittest discover -s tests -v` (7 tests, 100 % succès).

*Notes du présentateur :*  
La suite de tests s'exécute en moins de deux secondes et garantit la non-régression de l'algorithme sans avoir à retraiter les 456 Mo de ClinVar.

---

### Slide 10 : Conclusion et Perspectives
- **Objectif pleinement atteint :** Identification précise et ordonnée des gènes majeurs de la CMH.
- **Séparation claire :** Bash pour le streaming de gros volume, Python pour les statistiques et le graphe.
- **Perspectives d'évolution :**
  - Enrichissement avec le score de relecture clinique (`ReviewStatus` / étoiles ClinVar).
  - Intégration des variants de signification incertaine (*VUS*) via des outils de prédiction in silico (AlphaMissense, REVEL).
- **Merci pour votre attention ! Questions du jury.**

*Notes du présentateur :*  
Nous vous remercions de votre attention et sommes à votre disposition pour vos questions.
