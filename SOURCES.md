# Documentation des Sources de Données (SOURCES.md)

## 1. Identité et Origine du Jeu de Données

- **Organisme producteur :** National Center for Biotechnology Information (NCBI), National Library of Medicine (NLM), National Institutes of Health (NIH), États-Unis.
- **Base de données :** **ClinVar** (archive publique de rapports sur les relations entre les variations génomiques humaines et les phénotypes observés).
- **Fichier local utilisé :** `variant_summary_2026-10.txt.gz`
- **URL officielle communiquée pour le projet :**
  `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz`
- **URL de l'archive exacte utilisée :**
  `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/variant_summary_2026-10.txt.gz`
- **Version / Release utilisée :** `2026-10` (archive mensuelle NCBI ClinVar).
- **Date de vérification de l'URL officielle :** 04/11/2026.
- **Date de téléchargement du fichier local :** 04/11/2026.
- **Dernière modification annoncée par le serveur pour l'URL officielle :** 01/11/2026.

---

## 2. Caractéristiques Techniques et Intégrité

Les deux URL ne désignent pas nécessairement le même instantané. Pour garantir la reproductibilité, le pipeline utilise l'archive mensuelle d'octobre 2026, et non le fichier courant susceptible d'être actualisé.

| Propriété | Valeur vérifiée |
| :--- | :--- |
| **Nom du fichier local** | `variant_summary_2026-10.txt.gz` |
| **Nom du fichier dans l'archive** | `variant_summary_2026-10.txt.gz` |
| **Taille compressée** | 450 727 547 octets (~450,7 MB / 430 MiB) |
| **Format** | Fichier texte tabulé (TSV), compressé avec gzip |
| **SHA-256** | `a6a58df4d9049c9187a79a8fb4e70f1f3b5550e1708c6c74b7be0b268f5032da` |
| **Intégrité gzip** | Vérifiée avec `gzip -t` |
| **Taille décompressée** | 4 043 056 609 octets (~4,04 Go) |

Pour comparaison, lors de la vérification du 04/11/2026, l'URL officielle communiquée pour le projet répondait avec le statut HTTP `200 OK` et annonçait une taille de 457 862 838 octets. Cette taille concerne le fichier courant à cette URL et non l'archive mensuelle utilisée.

L'intégrité du fichier local est contrôlée automatiquement dans le pipeline `run.sh` par comparaison de l'empreinte cryptographique SHA-256 et par le test d'intégrité de l'archive gzip (`gzip -t`).


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
