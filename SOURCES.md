# Documentation des Sources de Données (SOURCES.md)

## 1. Identité et Origine du Jeu de Données

- **Organisme producteur :** National Center for Biotechnology Information (NCBI), National Library of Medicine (NLM), National Institutes of Health (NIH), États-Unis.
- **Base de données :** **ClinVar** (archive publique de rapports sur les relations entre les variations génomiques humaines et les phénotypes observés).
- **Fichier source :** `variant_summary.txt.gz`
- **URL officielle de téléchargement :**  
  `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz`
- **Répertoire FTP parent :**  
  `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/`
- **Version / Release :** `2026-10-19` (instantané hebdomadaire NCBI ClinVar).
- **Date de vérification et téléchargement :** 23/10/2026 (contrôlé le 30/10/2026).

---

## 2. Caractéristiques Techniques et Intégrité

| Propriété | Valeur |
| :--- | :--- |
| **Nom du fichier** | `variant_summary.txt.gz` |
| **Taille compressée (.gz)** | 456 505 123 octets (~456,5 Mo) |
| **Taille décompressée (.txt)** | 4 085 223 747 octets (~4,09 Go) |
| **Format** | Fichier texte tabulé (TSV), encodage UTF-8 / ASCII, compressé avec gzip |
| **Somme de contrôle SHA-256** | `b235cd5742ac615d55703672751fa3ea71c8222d5ff0547cd1e9b107fd8a647f` |
| **Somme de contrôle MD5** | `c79b46f3c02ef544608e0d9a83cac46e` |

L'intégrité du fichier téléchargé est contrôlée automatiquement dans le pipeline `run.sh` par comparaison de l'empreinte cryptographique SHA-256 et par le test d'intégrité de l'archive gzip (`gzip -t`).

---

## 3. Conditions de Réutilisation et Licence

- **Statut juridique :** Domaine public (*U.S. Government Work*, conformément à la section 105 du titre 17 du Code des États-Unis).
- **Conditions d'usage :** Les données de ClinVar sont mises à disposition gratuitement et sans restriction d'accès ou de propriété intellectuelle. Elles peuvent être librement redistribuées, modifiées, agrégées et utilisées pour des projets de recherche, d'enseignement ou d'application clinique.
- **Attribution requise :** Toute publication ou présentation exploitant ces données doit citer la base ClinVar et le NCBI conformément aux recommandations officielles de citation du NIH.

---

## 4. Nature et Structure des Données ClinVar

### 4.1. Niveau d'Agrégation du Fichier `variant_summary`
Une distinction scientifique fondamentale doit être soulignée :
> Le fichier `variant_summary.txt.gz` est un export **agrégé au niveau du variant** (`VariationID`). Le champ `ClinicalSignificance` représente l'évaluation synthétique de la pathogénicité calculée par ClinVar à partir de l'ensemble des soumissions de laboratoires et de panels d'experts.
> 
> **Important :** Ce décompte ne quantifie pas le nombre de patients, de familles ou de cas cliniques observés dans la population générale, mais bien le **nombre de variants distincts enregistrés dans ClinVar** portant une classification pathogène ou probablement pathogène.

### 4.2. Colonnes Exploitées par le Pipeline

1. **`VariationID`** (Entier) : Identifiant stable du variant dans ClinVar (utilisé comme unité de dénombrement unitaire).
2. **`GeneSymbol`** (Texte) : Symbole officiel du gène hôte selon la nomenclature HGNC (ex. *MYH7*, *MYBPC3*).
3. **`GeneID`** (Entier) : Identifiant du gène dans la base NCBI Entrez Gene.
4. **`ClinicalSignificance`** (Texte) : Classification clinique globale normalisée. Seuls `Pathogenic`, `Likely pathogenic` et `Pathogenic/Likely pathogenic` sont retenus.
5. **`PhenotypeList`** (Texte) : Liste de phénotypes / maladies associés au variant, séparés par le délimiteur `|`.
6. **`OriginSimple`** (Texte) : Origine allélique de la mutation. Seule la modalité `germline` est sélectionnée.
7. **`Assembly`** (Texte) : Assemblage génomique humain de référence. Seule la version moderne `GRCh38` est retenue.
8. **`ReviewStatus`** (Texte) : Statut de relecture scientifique (étoiles ClinVar / panels d'experts).
9. **`NumberSubmitters`** (Entier) : Nombre de centres ou laboratoires ayant soumis des preuves sur ce variant.
10. **`RCVaccession`** (Texte) : Identifiants d'accès RCV (*Record ClinVar Variant*) associés.
11. **`AlleleID`** (Entier) : Identifiant de l'allèle spécifique chez NCBI.

---

## 5. Phénotype Étudié : Cardiomyopathie Hypertrophique

- **Maladie :** Cardiomyopathie hypertrophique (CMH / HCM, *Hypertrophic Cardiomyopathy*).
- **Définition clinique :** Maladie cardiaque d'origine génétique caractérisée par un épaississement anormal du muscle myocardique (principalement le ventricule gauche), sans cause hypertensive ou valvulaire identifiable.
- **Règle de filtrage strict :** Pour éviter les faux positifs (par exemple, des syndromes métaboliques complexes ou des descriptions secondaires contenant le terme de manière incidente), l'élément de `PhenotypeList` doit être strictement égal à `Hypertrophic cardiomyopathy` ou `Hypertrophic cardiomyopathy <N>` (numéro de sous-type génétique facultatif, ex. HCM 1, HCM 4).

---

## 6. Références Bibliographiques Scientifiques

1. **Landrum MJ, Lee JM, Benson M, et al.** *ClinVar: improvements to access, data extraction and curation.* Nucleic Acids Research, 2020, 48(D1): D835–D844. DOI: [10.1093/nar/gkz972](https://doi.org/10.1093/nar/gkz972).
2. **Marian AJ, Braunwald E.** *Hypertrophic Cardiomyopathy: Genetics, Pathogenesis, Clinical Manifestations, Diagnostic Evaluation, and Prognosis.* Circulation Research, 2017, 121(7): 749–770. DOI: [10.1161/CIRCRESAHA.117.311059](https://doi.org/10.1161/CIRCRESAHA.117.311059).
3. **Richards S, Aziz N, Bale S, et al.** *Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology.* Genetics in Medicine, 2015, 17(5): 405–424. DOI: [10.1038/gim.2015.30](https://doi.org/10.1038/gim.2015.30).
