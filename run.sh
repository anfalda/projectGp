#!/usr/bin/env bash

set -Eeuo pipefail

readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEFAULT_CONFIG="$PROJECT_ROOT/config/dataset.env"
readonly RAW_DIR="$PROJECT_ROOT/data/raw"
readonly PROCESSED_DIR="$PROJECT_ROOT/data/processed"
readonly RESULTS_DIR="$PROJECT_ROOT/results"
readonly LOG_DIR="$PROJECT_ROOT/logs"
readonly TMP_ROOT="$PROJECT_ROOT/tmp"

CONFIG_FILE="$DEFAULT_CONFIG"
TOP_N=15
FORCE_DOWNLOAD=0
DRY_RUN=0
TEMP_DIR=""
LOG_FILE=""
PYTHON_CMD=""
PARTIAL_FILE=""

usage() {
    cat <<'EOF'
Usage: ./run.sh [options]

Pipeline ClinVar variant_summary - cardiomyopathie hypertrophique.

Options:
  -c FILE   Fichier de configuration (defaut: config/dataset.env)
  -t N      Nombre de genes dans la figure finale (defaut: 15)
  -f        Retelecharger les donnees meme si elles existent deja
  -n        Afficher le plan d'execution sans telecharger ni analyser
  -h        Afficher cette aide

Exemples:
  ./run.sh -h
  ./run.sh -n
  ./run.sh -t 20
EOF
}

log() {
    local level="$1"
    shift
    printf '[%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$level" "$*"
}

die() {
    log "ERREUR" "$*" >&2
    exit 1
}

cleanup() {
    local exit_code=$?
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf -- "$TEMP_DIR"
    fi
    if [[ -n "$PARTIAL_FILE" && -f "$PARTIAL_FILE" ]]; then
        rm -f -- "$PARTIAL_FILE"
    fi
    if (( exit_code != 0 )); then
        log "ERREUR" "Pipeline interrompu (code $exit_code). Consultez le journal: ${LOG_FILE:-non cree}." >&2
    fi
    exit "$exit_code"
}

on_signal() {
    log "ERREUR" "Signal recu; nettoyage des fichiers temporaires."
    exit 130
}

require_command() {
    local command_name="$1"
    command -v "$command_name" >/dev/null 2>&1 || die "Commande requise introuvable: $command_name"
}

resolve_python() {
    if [[ -n "${PYTHON_BIN:-}" ]]; then
        command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "Interpreteur Python introuvable: $PYTHON_BIN"
        "$PYTHON_BIN" --version >/dev/null 2>&1 || die "Interpreteur Python inutilisable: $PYTHON_BIN"
        PYTHON_CMD="$PYTHON_BIN"
    elif command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        die "Python 3 est requis mais aucun interpreteur utilisable n'a ete trouve."
    fi
}

setup_venv() {
    local venv_dir="$PROJECT_ROOT/.venv"
    if [[ ! -x "$venv_dir/bin/python" ]]; then
        log "INFO" "Creation de l'environnement virtuel"
        "$PYTHON_CMD" -m venv "$venv_dir" || die "venv impossible (installez python3-venv)."
    fi
    "$venv_dir/bin/pip" install --quiet -r "$PROJECT_ROOT/requirements.txt" || die "Installation des dependances impossible."
    PYTHON_CMD="$venv_dir/bin/python"
    export MPLBACKEND=Agg
}

ensure_directories() {
    mkdir -p "$RAW_DIR" "$PROCESSED_DIR" "$RESULTS_DIR" "$LOG_DIR" "$TMP_ROOT"
    TEMP_DIR="$(mktemp -d "$TMP_ROOT/run.XXXXXX")"
}

load_config() {
    [[ -f "$CONFIG_FILE" ]] || die "Fichier de configuration introuvable: $CONFIG_FILE"
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"

    local required_vars=(CLINVAR_RELEASE VARIANT_FILENAME VARIANT_URL VARIANT_SHA256)
    local variable
    for variable in "${required_vars[@]}"; do
        [[ -n "${!variable:-}" ]] || die "Variable vide dans la configuration: $variable"
    done
}

validate_config_ready() {
    [[ "$VARIANT_SHA256" != TODO_* ]] || die "VARIANT_SHA256 doit etre defini dans config/dataset.env."
    [[ "$VARIANT_SHA256" =~ ^[[:xdigit:]]{64}$ ]] || die "VARIANT_SHA256 doit contenir 64 caracteres hexadecimaux."
}

validate_positive_integer() {
    [[ "$TOP_N" =~ ^[1-9][0-9]*$ ]] || die "L'option -t attend un entier strictement positif."
}

sha256_of() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        die "Impossible de calculer SHA-256: installez sha256sum ou shasum."
    fi
}

verify_file() {
    local file="$1"
    local expected_sha="$2"
    local actual_sha

    [[ -f "$file" ]] || die "Fichier manquant: $file"
    actual_sha="$(sha256_of "$file")"
    [[ "${actual_sha,,}" == "${expected_sha,,}" ]] || die "Somme SHA-256 incorrecte pour $(basename "$file")."
    gzip -t "$file" || die "Archive gzip invalide: $file"
    log "OK" "Integrite verifiee: $(basename "$file")"
}

download_file() {
    local url="$1"
    local destination="$2"
    local expected_sha="$3"
    local partial="$destination.part"
    PARTIAL_FILE="$partial"

    if [[ -f "$destination" && "$FORCE_DOWNLOAD" -eq 0 ]]; then
        log "INFO" "Fichier deja present: $(basename "$destination")"
        verify_file "$destination" "$expected_sha"
        chmod a-w "$destination"
        return
    fi

    if [[ -f "$destination" ]]; then
        chmod u+w "$destination" 2>/dev/null || true
        rm -f -- "$destination"
    fi
    log "INFO" "Telechargement de $(basename "$destination")"
    local attempt=1
    until curl --fail --location --continue-at - --retry 3 --retry-delay 5 --output "$partial" "$url"; do
        (( attempt < 10 )) || die "Telechargement impossible apres 10 tentatives."
        log "WARN" "Telechargement interrompu, reprise (tentative $attempt/10)"
        attempt=$((attempt + 1))
        sleep 5
    done
    mv -- "$partial" "$destination"
    PARTIAL_FILE=""
    verify_file "$destination" "$expected_sha"
    chmod a-w "$destination"
}

run_shell_filter() {
    local variant_file="$1"
    local filtered_file="$PROCESSED_DIR/hcm_variants_grch38.tsv"

    log "INFO" "Filtrage GRCh38, germline et phenotype HCM strict"
    "$PROJECT_ROOT/scripts/filter_hcm_variants.sh" "$variant_file" "$filtered_file"
    [[ -s "$filtered_file" ]] || die "Le filtrage n'a produit aucune donnee."
}

run_python_analysis() {
    local script="$PROJECT_ROOT/scripts/analyze_genes.py"
    local filtered_file="$PROCESSED_DIR/hcm_variants_grch38.tsv"

    [[ -f "$script" ]] || die "Analyse Python manquante: scripts/analyze_genes.py"
    log "INFO" "Analyse Python et creation des resultats"
    "$PYTHON_CMD" "$script" --variants "$filtered_file" --output-dir "$RESULTS_DIR" --top "$TOP_N"
}

archive_results() {
    local timestamp archive output
    local expected_outputs=(gene_ranking.csv variants_hcm.csv excluded_variants.csv summary.json top_genes.png)

    for output in "${expected_outputs[@]}"; do
        [[ -s "$RESULTS_DIR/$output" ]] || die "Resultat attendu manquant: results/$output"
    done

    timestamp="$(date '+%Y%m%d_%H%M%S')"
    archive="$RESULTS_DIR/resultats_${timestamp}.tar.gz"
    tar -czf "$archive" -C "$RESULTS_DIR" "${expected_outputs[@]}"
    log "OK" "Resultats archives: $archive"
}

show_results() {
    log "INFO" "Classement des ${TOP_N} premiers genes (results/gene_ranking.csv)"
    head -n "$((TOP_N + 1))" "$RESULTS_DIR/gene_ranking.csv" \
        | awk -F, '{printf "%-6s %-12s %-22s %s\n", $1, $2, $3, $4}'
}

print_plan() {
    cat <<EOF
Version ClinVar : $CLINVAR_RELEASE
Configuration   : $CONFIG_FILE
Donnees         : $VARIANT_URL
Filtres         : GRCh38 -> germline -> libelle HCM exact -> P/LP -> VariationID distincts
Etapes          : telechargement -> verification -> filtrage Shell -> analyse Python -> archive
Top genes       : $TOP_N
EOF
}

while getopts ":c:t:fnh" option; do
    case "$option" in
        c) CONFIG_FILE="$OPTARG" ;;
        t) TOP_N="$OPTARG" ;;
        f) FORCE_DOWNLOAD=1 ;;
        n) DRY_RUN=1 ;;
        h) usage; exit 0 ;;
        :) die "L'option -$OPTARG exige une valeur." ;;
        \?) die "Option inconnue: -$OPTARG. Utilisez -h pour l'aide." ;;
    esac
done

shift $((OPTIND - 1))
(( $# == 0 )) || die "Argument inattendu: $1"

trap cleanup EXIT
trap on_signal INT TERM HUP

validate_positive_integer
load_config

if (( DRY_RUN == 1 )); then
    print_plan
    exit 0
fi

validate_config_ready
ensure_directories
LOG_FILE="$LOG_DIR/run_$(date '+%Y%m%d_%H%M%S').log"
exec > >(tee -a "$LOG_FILE") 2>&1

require_command curl
require_command gzip
require_command awk
require_command sort
require_command uniq
require_command tar
require_command tee
require_command mktemp
resolve_python
setup_venv

log "INFO" "Demarrage du pipeline ClinVar $CLINVAR_RELEASE"
variant_path="$RAW_DIR/$VARIANT_FILENAME"
download_file "$VARIANT_URL" "$variant_path" "$VARIANT_SHA256"
run_shell_filter "$variant_path"
run_python_analysis
archive_results
show_results
log "OK" "Pipeline termine avec succes."
