# Rapport Scientifique et Technique

## Analyse des Variants Génétiques de la Cardiomyopathie Hypertrophique dans ClinVar

---

**Groupe de Projet :** Groupe d'Ingénierie Génomique & Administration Système  
**Établissement :** Université Amar Telidji de Laghouat  
**Date :** Octobre 2026  
**Dépôt GitHub officiel :** [https://github.com/ffmly/redesigned-spoon](https://github.com/ffmly/redesigned-spoon)

---

### Résumé Exécutif

Ce projet met en œuvre une infrastructure logicielle automatisée, associant scripts Shell POSIX et programme d'analyse Python 3, pour répondre à une question centrale en génétique cardiologique : **Quels gènes concentrent le plus de variants distincts classés « Pathogenic » ou « Likely pathogenic » dans la base de référence NCBI ClinVar, spécifiquement associés à la cardiomyopathie hypertrophique (CMH) ?**  
À partir d'un jeu de données brut de 456,5 Mo compressé (plus de 4,08 Go décompressé), notre chaîne de filtrage en flux streaming a extrait 17 027 enregistrements germlinaires sur l'assemblage humain de référence GRCh38. Après normalisation rigoureuse des classifications cliniques et dédoublonnage strict par identifiant de variant (`VariationID`), **1 435 variants pathogènes ou probablement pathogènes distincts** ont été identifiés sur un ensemble de **40 gènes**. Les deux gènes sarcomériques majeurs, **MYBPC3** (838 variants, 58,40 %) et **MYH7** (308 variants, 21,46 %), concentrent à eux seuls **79,86 %** de l'ensemble des variants délétères répertoriés, en parfaite adéquation avec la littérature médicale internationale.

---

## 1. Introduction et Problématique Médicale

### 1.1. Contexte Physiopathologique de la Cardiomyopathie Hypertrophique
La cardiomyopathie hypertrophique (CMH ou *HCM*, *Hypertrophic Cardiomyopathy*) est l'affection cardiovasculaire d'origine monogénique la plus fréquente, avec une prévalence estimée à environ **1 individu sur 500** dans la population adulte générale. Elle est définie cliniquement par un épaississement myocardique inapproprié (hypertrophie ventriculaire gauche avec épaisseur pariétale $\ge 15\text{ mm}$ en échocardiographie ou IRM cardiaque), survenant en l'absence de condition hémodynamique anormale telle qu'une sténose aortique ou une hypertension artérielle sévère.  
Cliniquement hétérogène, la CMH s'étend de formes asymptomatiques de découverte fortuite jusqu'à des complications dramatiques : insuffisance cardiaque réfractaire, accidents thromboemboliques et surtout **mort subite par fibrillation ventriculaire**, particulièrement chez les jeunes sportifs de haut niveau.

### 1.2. Rôle du Diagnostic Génétique et Base ClinVar
Depuis la découverte initiale des mutations du gène *MYH7* dans les années 1990, la CMH est reconnue comme la « maladie du sarcomère », transmise selon un mode autosomique dominant à pénétrance variable. La base de données **ClinVar** de la *National Library of Medicine* (NCBI/NIH) constitue aujourd'hui le registre mondial d'agrégation des assertions cliniques sur les variants du génome humain.  
Cependant, l'hétérogénéité des soumissions et l'accumulation de variants de signification incertaine (*VUS*) imposent une méthodologie de filtrage strict pour isoler les gènes réellement porteurs de mutations délétères avérées.

### 1.3. Objectif et Définition de l'Unité de Mesure
Notre étude vise à établir le palmarès quantitatif des gènes impliqués dans la CMH.  
> **Distinction scientifique essentielle :** Nous quantifions le **nombre de variants distincts répertoriés** (`VariationID` unitaire dans ClinVar) et non le nombre de patients ou la prévalence clinique dans les cohortes hospitalières. Notre résultat caractérise le paysage mutationnel documenté dans les bases de données publiques de diagnostic moléculaire.

---

## 2. Données et Méthodologie d'Analyse

### 2.1. Données Brutes et Contrôle d'Intégrité
Le jeu de données officiel utilisé est l'export tabulé public de NCBI ClinVar :
- **Fichier :** `variant_summary.txt.gz` (Release 2026-10-19)
- **Taille :** 456 505 123 octets (~456,5 Mo compressé, 4 085 223 747 octets décompressé)
- **Empreinte SHA-256 :** `b235cd5742ac615d55703672751fa3ea71c8222d5ff0547cd1e9b107fd8a647f`

Le script d'orchestration `run.sh` assure le téléchargement idempotent via `curl`, contrôle automatiquement l'empreinte SHA-256 et valide l'intégrité de l'archive par `gzip -t`. Dès validation, le fichier brut est protégé en lecture seule (`chmod a-w`).

### 2.2. Étape 1 : Filtrage Haute Performance en Flux Shell POSIX
Décompresser un fichier de 4,1 Go sur disque saturerait inutilement les entrées/sorties. Le script `scripts/filter_hcm_variants.sh` utilise une chaîne de traitement en flux continu connectant plus de trois commandes par tubes (*pipes*) :
$$\text{gzip -cd} \;\longrightarrow\; \text{awk (sélection conditionnelle)} \;\longrightarrow\; \text{sort} \;\longrightarrow\; \text{uniq}$$

Les critères de sélection stricts appliqués sont :
1. **Assemblage génomique :** `Assembly == "GRCh38"` (élimination des redondances obsolètes de GRCh37/hg19).
2. **Origine allélique :** `tolower(OriginSimple) == "germline"` (exclusion des altérations somatiques tumorales).
3. **Phénotype spécifique :** Recherche stricte dans `PhenotypeList` (délimitée par `|`) de l'intitulé exact `Hypertrophic cardiomyopathy` (avec numéro de sous-type facultatif, ex. CMH 1 à 20). Une simple inclusion du terme au sein d'une maladie mitochondriale ou syndromique différente est rejetée.

Cette étape extrait **17 027 lignes pertinentes** écrites dans `data/processed/hcm_variants_grch38.tsv`.

### 2.3. Étape 2 : Normalisation, Dédoublonnage et Analyse Python
Le script `scripts/analyze_genes.py` traite le fichier filtré selon des règles d'ingénierie logicielle strictes :
1. **Normalisation de la pathogénicité :** Seules les classifications canoniques `Pathogenic`, `Likely pathogenic` et `Pathogenic/Likely pathogenic` sont acceptées. Les variants bénins, bénins probables, les significations incertaines (*VUS*, 7 930 occurrences) et les classifications conflictuelles (1 944 occurrences) sont exclus et tracés dans `results/excluded_variants.csv`.
2. **Normalisation du symbole de gène :** Validation selon la nomenclature HGNC. Les symboles manquants (`-`, vide, `NA`) ou ambigus (variants multi-gènes séparés par `;` ou annotations complexes de remaniements) sont exclus du classement unitaire.
3. **Dédoublonnage unitaire par `VariationID` :** Dans ClinVar, un même variant peut comporter plusieurs allèles ou soumissions. Chaque `VariationID` distinct n'est comptabilisé qu'une seule fois par gène.

---

## 3. Résultats et Discussion Biologique

### 3.1. Synthèse Statistique Globale
Le traitement produit une classification nette et traçable :

| Métrique | Valeur | Pourcentage |
| :--- | :---: | :---: |
| Enregistrements analysés (GRCh38, germline, HCM) | 17 027 | 100,00 % |
| Variants exclus (VUS, bénins, conflictuels, multi-gènes) | 15 592 | 91,57 % |
| **Variants pathogènes / probablement pathogènes retenus** | **1 435** | **8,43 %** |
| **Nombre total de gènes distincts impliqués** | **40** | — |

### 3.2. Classement des Principaux Gènes Associés à la CMH
Le tableau ci-dessous présente les 15 premiers gènes concentrant le plus grand nombre de variants délétères distincts dans ClinVar :

| Rang | Gène | Nombre de variants distincts | Part des variants retenus (%) | Rôle fonctionnel principal |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **MYBPC3** | **838** | **58,40 %** | Protéine sarcomérique C de liaison à la myosine |
| **2** | **MYH7** | **308** | **21,46 %** | Chaîne lourde de bêta-myosine (filament épais) |
| **3** | **FLNC** | **66** | **4,60 %** | Filamine C (cytosquelette et disque Z) |
| **4** | **TNNI3** | **56** | **3,90 %** | Troponine I cardiaque (complexe régulateur du filament fin) |
| **5** | **TNNT2** | **32** | **2,23 %** | Troponine T2 cardiaque (liaison tropomyosine) |
| **6** | **TPM1** | **24** | **1,67 %** | Alpha-tropomyosine 1 |
| **7** | **TTN** | **15** | **1,05 %** | Titine (cohésion mécanique élastique) |
| **8** | **PRKAG2** | **11** | **0,77 %** | Sous-unité gamma-2 AMPK (phénocopie métabolique) |
| **9** | **MYL2** | **10** | **0,70 %** | Chaîne légère régulatrice de myosine |
| **10** | **ALPK3** | **8** | **0,56 %** | Alpha-kinase 3 (intégrité sarcomérique) |
| **11** | **MYH7B** | **8** | **0,56 %** | Chaîne lourde de myosine 7B / microARN miR-499 |
| **12** | **LAMP2** | **7** | **0,49 %** | Protéine membranaire lysosomale (maladie de Danon) |
| **13** | **MYH6** | **5** | **0,35 %** | Chaîne lourde d'alpha-myosine cardiaque |
| **14** | **TCAP** | **5** | **0,35 %** | Téléthonine / Titin-cap (disque Z) |
| **15** | **ACTC1** | **4** | **0,28 %** | Actine alpha-cardiaque (filament fin) |

### 3.3. Analyse et Confrontation avec la Littérature Médicale

#### 1. L'hégémonie sarcomérique : le tandem MYBPC3 / MYH7
Notre pipeline révèle que **MYBPC3** (58,40 %) et **MYH7** (21,46 %) représentent ensemble **79,86 %** des variants pathogènes répertoriés. Ce résultat concorde remarquablement avec les revues de référence de Marian & Braunwald (*Circulation Research*, 2017), qui rapportent que les mutations de *MYBPC3* et *MYH7* constituent environ 70 à 80 % de tous les génotypes positifs identifiés chez les patients atteints de CMH.
- *MYBPC3* présente une diversité considérable de variants tronquants (mutations non-sens, décalages du cadre de lecture et anomalies d'épissage), agissant majoritairement par **haplo-insuffisance**.
- *MYH7* est au contraire dominé par des mutations faux-sens (*missense*) siégeant principalement dans le domaine céphalique moteur (tête globulaire S1), exerçant un effet **dominant-négatif** par altération de l'activité ATPasique et de la force unitaire générée.

#### 2. Les régulateurs du filament fin (TNNI3, TNNT2, TPM1, ACTC1)
Ces gènes encadrent la sensibilité sarcomérique au calcium intracellulaire ($Ca^{2+}$). Bien que représentant un volume de variants plus réduit (environ 8 % au total), les variants de *TNNT2* sont reconnus pour conférer un risque arythmogène élevé avec possibilité de mort subite précoce malgré une hypertrophie ventriculaire morphologique souvent modeste.

#### 3. Les gènes non-sarcomériques et phénocopies métaboliques
ClinVar met en lumière des gènes émergents ou des phénocopies :
- **FLNC (Filamine C) :** Troisième gène du classement (4,60 %), impliqué dans l'architecture du disque Z. Les mutations de FLNC sont fréquemment associées à des formes de cardiomyopathies restrictives et hypertrophiques à haut potentiel d'arythmie ventriculaire maligne.
- **PRKAG2 et LAMP2 :** Ces gènes ne codent pas pour des éléments contractiles mais correspondent à des maladies de surcharge (glycogénose cardiaque pour PRKAG2 avec syndrome de Wolff-Parkinson-White ; maladie de Danon liée à l'X pour LAMP2). Leur présence dans ClinVar reflète l'importance du diagnostic différentiel génétique face à une hypertrophie cardiaque.

---

## 4. Administration Système, Reproductibilité et Limites

### 4.1. Conformité aux Standards d'Administration Système
L'orchestration du projet respecte les règles fondamentales de robustesse :
- **Conformité POSIX et Bash strict :** Utilisation de `set -Eeuo pipefail` interdisant les variables non définies et propageant immédiatement les erreurs de pipelines.
- **Modularité des fonctions réutilisables :** Définition centralisée de `log()`, `die()`, `require_command()`, `verify_file()`.
- **Analyse des options par `getopts` :** Gestion des options `-c`, `-t`, `-f`, `-n`, `-h`.
- **Gestion des signaux et nettoyage temporaire :** Utilisation de `trap cleanup EXIT` et `trap on_signal INT TERM HUP`, garantissant l'effacement des répertoires temporaires `tmp/run.XXXXXX`.
- **Traçabilité totale :** Chaque exécution crée un journal horodaté `logs/run_YYYYMMDD_HHMMSS.log` capturant les flux `stdout` et `stderr`.
- **Automatisation planifiée :** Mise à disposition du fichier `cron/clinvar_pipeline.cron` pour le rafraîchissement mensuel automatique des données.

### 4.2. Validation par Tests Automatiques
Le module `tests/test_analyze_genes.py` implémente une batterie de tests unitaires avec le framework Python standard `unittest`. Les tests valident le dédoublonnage, l'élimination des variants non pathogènes et le tri sans mobiliser le fichier volumineux de 456 Mo, assurant des tests d'intégration continue instantanés et reproductibles.

### 4.3. Limites de l'Étude
1. **Biais de soumission ClinVar :** ClinVar est une base contributive. Les gènes historiquement connus et systématiquement inclus dans les panels NGS hospitaliers (*MYBPC3*, *MYH7*) concentrent davantage de soumissions que des gènes plus récemment décrits (*ALPK3*).
2. **Non-équivalence à la prévalence épidémiologique :** Un variant récurrent porté par des milliers d'individus dans une population compte pour une unité (`VariationID`), exactement comme un variant privé observé dans une seule famille.
3. **Variants de signification incertaine (VUS) :** 7 930 variants filtrés ont été écartés en raison de preuves fonctionnelles ou familiales insuffisantes. Les futures réévaluations de ClinVar permettront de reclasser une fraction d'entre eux.

---

## 5. Conclusion

Ce projet a permis de concevoir une chaîne de traitement complète, performante et rigoureusement documentée. L'analyse met en évidence le rôle écrasant des gènes sarcomériques dans la cardiomyopathie hypertrophique, avec une primauté incontestable de **MYBPC3** (58,40 %) et **MYH7** (21,46 %).  
L'architecture logicielle développée garantit une reproductibilité intégrale, une gestion propre des erreurs système et une traçabilité totale des données de la source brute jusqu'à la figure scientifique finale.

---

## Références Bibliographiques

1. **Landrum MJ, Lee JM, Benson M, et al.** ClinVar: improvements to access, data extraction and curation. *Nucleic Acids Res.* 2020;48(D1):D835-D844.
2. **Marian AJ, Braunwald E.** Hypertrophic Cardiomyopathy: Genetics, Pathogenesis, Clinical Manifestations, Diagnostic Evaluation, and Prognosis. *Circ Res.* 2017;121(7):749-770.
3. **Richards S, Aziz N, Bale S, et al.** Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology. *Genet Med.* 2015;17(5):405-424.
4. **Ommen SR, Mital S, Burke MA, et al.** 2020 AHA/ACC Guideline for the Diagnosis and Treatment of Patients With Hypertrophic Cardiomyopathy. *Circulation.* 2020;142(25):e533-e557.
