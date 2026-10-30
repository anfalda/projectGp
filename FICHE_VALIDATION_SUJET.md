# Fiche de validation du sujet

**Groupe :** Groupe n° 1 (Génétique Médicale et Administration Système)

**Membres :**

1. Benamara Ahmed Ryad (Étudiant 1 — Orchestration générale et filtre Shell)
2. Étudiant 2 (Source des données, intégrité cryptographique SHA-256 et SOURCES.md)
3. Étudiant 3 (Développement de l'analyse Python et tests unitaires automatisés)
4. Étudiant 4 (Environnement, planification cron, gestion des permissions et logs)
5. Étudiant 5 (Documentation, rapport scientifique, présentation et validation)

**Sujet envisage :** Quels genes concentrent le plus de variants distincts
classes « Pathogenic » ou « Likely pathogenic » dans ClinVar, associes
specifiquement a la cardiomyopathie hypertrophique ?

**Maladie etudiee :** Cardiomyopathie hypertrophique (CMH / HCM).

**Jeu de donnees :** `variant_summary.txt.gz`, export tabule public de NCBI
ClinVar.

**Lien :**
https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz

**Taille estimee :** 456 505 123 octets, soit environ 456,5 Mo au format
compresse `.gz` (4 085 223 747 octets decompresse).

**Date de verification :** 23/10/2026 (controle le 30/10/2026).

**Somme de controle SHA-256 :**
`b235cd5742ac615d55703672751fa3ea71c8222d5ff0547cd1e9b107fd8a647f`

**Methode prevue :** conserver l'assemblage GRCh38 et l'origine germinale,
identifier dans `PhenotypeList` un libelle exact `Hypertrophic cardiomyopathy`
avec un numero de sous-type facultatif, puis retenir les classifications
`Pathogenic`, `Likely pathogenic` et `Pathogenic/Likely pathogenic`. Chaque
`VariationID` sera comptee une seule fois. Les lignes sans gene et les
classifications non retenues seront documentees separement.
