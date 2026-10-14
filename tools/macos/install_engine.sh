#!/bin/bash
# Shared, noninteractive installer. Bash 3.2 compatible, no Python dependency.
set -euo pipefail
PAYLOAD="$1"
USER_HOME="$2"
USER_UID="$3"
USER_GID="$4"
VERSION="$5"
case "$USER_HOME" in /Users/*) ;; *) echo 'Conta de usuário inválida.' >&2; exit 1;; esac
case "$USER_UID" in ''|*[!0-9]*) exit 1;; esac
[ "$USER_UID" -ge 501 ] || { echo 'Não instale na conta root ou em uma conta de sistema.' >&2; exit 1; }
for part in 'Titan Titles Studio.py' titan_update.py titan_locale.py titan_sfx.py caption-bin.drb THIRD_PARTY_NOTICES.md icons sfx; do
    [ -e "$PAYLOAD/$part" ] || { echo "Pacote incompleto: $part" >&2; exit 1; }
done
assert_path() {
    local path="$1" current
    case "$path" in "$USER_HOME/Library/"*|'/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/'*) ;; *) echo "Destino inválido: $path" >&2; exit 1;; esac
    current="$path"
    while [ "$current" != / ]; do
        [ ! -L "$current" ] || { echo "Destino redirecionado: $current" >&2; exit 1; }
        current=$(/usr/bin/dirname "$current")
    done
}
TARGETS=("$USER_HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit")
CONTAINER="$USER_HOME/Library/Containers/com.blackmagic-design.DaVinciResolveApp"
if [ -d "$CONTAINER" ]; then
    TARGETS+=("$CONTAINER/Data/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit")
fi
MOVED_FROM=()
MOVED_TO=()
CREATED=()
STAGES=()
SUCCESS=no
RETIRED_COUNT=0
rollback() {
    local status=$? i
    if [ "$SUCCESS" != yes ]; then
        for ((i=${#CREATED[@]}-1; i>=0; i--)); do
            assert_path "${CREATED[$i]}"
            /bin/rm -rf "${CREATED[$i]}"
        done
        for ((i=${#MOVED_FROM[@]}-1; i>=0; i--)); do
            if [ -e "${MOVED_TO[$i]}" ]; then
                /bin/mkdir -p "$(/usr/bin/dirname "${MOVED_FROM[$i]}")"
                /bin/mv "${MOVED_TO[$i]}" "${MOVED_FROM[$i]}"
            fi
        done
        echo 'Instalação interrompida; versão anterior restaurada.' >&2
    fi
    for ((i=0; i<${#STAGES[@]}; i++)); do /bin/rm -rf "${STAGES[$i]}"; done
    return "$status"
}
trap rollback EXIT
retire() {
    local old="$1" saved="$2"
    assert_path "$old"
    if [ -e "$old" ]; then
        /bin/mv "$old" "$saved"
        MOVED_FROM+=("$old")
        MOVED_TO+=("$saved")
    fi
}
clean_menu() {
    local scripts="$1" backup="$2" active="$3" file name
    [ -d "$scripts" ] || return 0
    assert_path "$scripts/Edit"
    while IFS= read -r -d '' file; do
        [ "$file" != "$active" ] || continue
        name="$(/usr/bin/basename "$file")"
        RETIRED_COUNT=$((RETIRED_COUNT+1))
        retire "$file" "$backup/menu-$RETIRED_COUNT-$name"
    done < <(/usr/bin/find "$scripts" -type f \( -iname 'Titan Studio*.py' -o -iname 'Titan Titles Studio*.py' -o -iname 'Titan Titulo Studio*.py' -o -iname 'Titan Títulos Studio*.py' -o -iname 'Titan Studio*.lua' -o -iname 'Titan Titles Studio*.lua' -o -iname 'Titan Titulo Studio*.lua' -o -iname 'titan_update.py' -o -iname 'titan_locale.py' -o -iname 'titan_sfx.py' -o -iname 'Titan Update.py' \) -print0)
    for name in TitanTitlesStudio TitanTitlesStudio-backups; do
        retire "$scripts/Edit/$name" "$backup/legacy-$name"
    done
}
# Validate all locations before making the first change.
for target in "${TARGETS[@]}"; do
    fusion="$(/usr/bin/dirname "$(/usr/bin/dirname "$target")")"
    for path in "$target" "$fusion/TitanTitlesStudio" "$fusion/TitanTitlesStudio-backups" "$target/Titan Studio.py"; do assert_path "$path"; done
done
FIRST_BACKUP=''
for target in "${TARGETS[@]}"; do
    fusion="$(/usr/bin/dirname "$(/usr/bin/dirname "$target")")"
    resources="$fusion/TitanTitlesStudio"
    /bin/mkdir -p "$target" "$fusion/TitanTitlesStudio-backups"
    backup=$(/usr/bin/mktemp -d "$fusion/TitanTitlesStudio-backups/pkg-$VERSION-XXXXXXXX")
    [ -n "$FIRST_BACKUP" ] || FIRST_BACKUP="$backup"
    stage=$(/usr/bin/mktemp -d "$fusion/.titan-stage-XXXXXXXX")
    STAGES+=("$stage")
    /bin/mkdir "$stage/TitanTitlesStudio"
    /usr/bin/ditto "$PAYLOAD/icons" "$stage/TitanTitlesStudio/icons"
    /usr/bin/install -m 644 "$PAYLOAD/titan_update.py" "$stage/TitanTitlesStudio/titan_update.py"
    /usr/bin/install -m 644 "$PAYLOAD/titan_locale.py" "$stage/TitanTitlesStudio/titan_locale.py"
    /usr/bin/install -m 644 "$PAYLOAD/titan_sfx.py" "$stage/TitanTitlesStudio/titan_sfx.py"
    /usr/bin/install -m 644 "$PAYLOAD/caption-bin.drb" "$stage/TitanTitlesStudio/caption-bin.drb"
    /usr/bin/install -m 644 "$PAYLOAD/THIRD_PARTY_NOTICES.md" "$stage/TitanTitlesStudio/THIRD_PARTY_NOTICES.md"
    /usr/bin/ditto "$PAYLOAD/sfx" "$stage/TitanTitlesStudio/sfx"
    /usr/bin/install -m 644 "$PAYLOAD/Titan Titles Studio.py" "$stage/Titan Studio.py"
    printf '%s\n' "$VERSION" > "$stage/TitanTitlesStudio/installed-version.txt"
    if [ "$(/usr/bin/id -u)" = 0 ]; then /usr/sbin/chown -R "$USER_UID:$USER_GID" "$stage"; fi
    retire "$resources" "$backup/resources-before"
    retire "$target/Titan Studio.py" "$backup/Titan Studio.py"
    /bin/mv "$stage/TitanTitlesStudio" "$resources"
    CREATED+=("$resources")
    /bin/mv "$stage/Titan Studio.py" "$target/Titan Studio.py"
    CREATED+=("$target/Titan Studio.py")
    clean_menu "$(/usr/bin/dirname "$target")" "$backup" "$target/Titan Studio.py"
    if [ "$(/usr/bin/id -u)" = 0 ]; then
        /usr/sbin/chown "$USER_UID:$USER_GID" "$target" "$fusion" "$fusion/TitanTitlesStudio-backups"
        /usr/sbin/chown -R "$USER_UID:$USER_GID" "$backup"
    fi
done
# Remove duplicate global Titan scripts too; unrelated scripts are never selected.
if [ "$(/usr/bin/id -u)" = 0 ]; then
    clean_menu '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts' "$FIRST_BACKUP" ''
fi
SUCCESS=yes
echo "Titan Titles Studio $VERSION instalado. Menu: Workspace > Scripts > Edit > Titan Studio"
echo "Backup: $FIRST_BACKUP"
