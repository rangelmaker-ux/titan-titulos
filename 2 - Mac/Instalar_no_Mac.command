#!/bin/bash
set -euo pipefail
DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
TARGET="$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit"
STORE="$HOME/Library/Containers/com.blackmagic-design.DaVinciResolveApp/Data/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit"
printf '\033[38;2;56;189;248m\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n  TITAN TITLES STUDIO  •  v3.2.2\n  TITÂNIO & AZUL ELÉTRICO  •  @rangelmaker_\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n'
printf '\nLayouts, tipografia e movimento para DaVinci Resolve.\nAtualizações pelo GitHub com backup automático.\n\n'
ACTION=$(/usr/bin/osascript <<'APPLESCRIPT'
button returned of (display dialog "Seu próximo título começa aqui.\n\nFeche o Titan antes de instalar ou remover.\nAtualizações pelo GitHub com backup automático." with title "Titan Titles Studio" buttons {"Cancelar", "Remover", "Instalar"} default button "Instalar" cancel button "Cancelar")
APPLESCRIPT
) || exit 0
CLEAN=no
if [ "$ACTION" = "Instalar" ]; then
    for part in "Titan Titles Studio.py" "titan_update.py" "icons"; do
        if [ ! -e "$DIR/$part" ]; then
            /usr/bin/osascript -e 'display alert "Titan Titles Studio" message "Pacote incompleto. Extraia o ZIP inteiro antes de instalar." as critical'
            exit 1
        fi
    done
    CLEAN=$(/usr/bin/osascript <<'APPLESCRIPT'
button returned of (display dialog "Deseja remover os arquivos da versão Titan anterior antes de reinstalar?\n\nUm backup será preservado. Outros plugins não serão removidos." with title "Titan Titles Studio" buttons {"Cancelar", "Manter", "Remover antiga"} default button "Manter" cancel button "Cancelar")
APPLESCRIPT
    ) || exit 0
else
    /usr/bin/osascript -e 'display dialog "Remover o Titan Titles Studio? Um backup será preservado. Outros plugins não serão removidos." with title "Titan Titles Studio" buttons {"Cancelar", "Remover"} default button "Cancelar" cancel button "Cancelar"' >/dev/null || exit 0
fi
validate() {
    case "$1" in "$TARGET"|"$STORE") ;; *) echo 'Destino inesperado.'; exit 1;; esac
    local current="$1"
    while [ "$current" != / ]; do
        if [ -L "$current" ]; then echo 'Pasta redirecionada; instalação interrompida.'; exit 1; fi
        current=$(dirname "$current")
    done
    local storage="$(dirname "$(dirname "$1")")"
    for current in "$storage/TitanTitlesStudio" "$storage/TitanTitlesStudio-backups" "$1/Titan Studio.py" "$1/Titan Titles Studio.py" "$1/TitanTitlesStudio" "$1/TitanTitlesStudio-backups"; do
        if [ -L "$current" ]; then echo 'Arquivo redirecionado; instalação interrompida.'; exit 1; fi
    done
}
install_target() {
    local target="$1" backup storage
    storage="$(dirname "$(dirname "$target")")"
    validate "$target"
    mkdir -p "$target"
    mkdir -p "$storage/TitanTitlesStudio-backups"
    backup=$(mktemp -d "$storage/TitanTitlesStudio-backups/install-XXXXXXXX")
    [ ! -f "$target/Titan Studio.py" ] || cp -p "$target/Titan Studio.py" "$backup/"
    [ ! -d "$storage/TitanTitlesStudio" ] || cp -R "$storage/TitanTitlesStudio" "$backup/"
    if [ "$ACTION" = "Remover" ] || [ "$CLEAN" = "Remover antiga" ]; then
        rm -f "$target/Titan Studio.py"
        rm -rf "$storage/TitanTitlesStudio"
    fi
    if [ "$ACTION" = "Instalar" ]; then
        if ! (mkdir -p "$storage/TitanTitlesStudio" && cp -R "$DIR/icons" "$storage/TitanTitlesStudio/" && cp "$DIR/titan_update.py" "$storage/TitanTitlesStudio/" && cp "$DIR/Titan Titles Studio.py" "$target/Titan Studio.py"); then
            rm -f "$target/Titan Studio.py"
            rm -rf "$storage/TitanTitlesStudio"
            [ ! -f "$backup/Titan Studio.py" ] || cp "$backup/Titan Studio.py" "$target/"
            [ ! -d "$backup/TitanTitlesStudio" ] || cp -R "$backup/TitanTitlesStudio" "$storage/"
            echo "Falha. Backup: $backup"
            return 1
        fi
    fi
    for name in "Titan Titles Studio.py" "Titan Titulo Studio.py" "Titan Titles Studio Backup.py" "Titan Titulo Studio Backup.py" "Titan Update.py" "titan_update.py" "TitanTitlesStudio" "TitanTitlesStudio-backups"; do
        if [ -e "$target/$name" ]; then
            if [ -L "$target/$name" ]; then echo 'Arquivo antigo redirecionado.'; return 1; fi
            mv "$target/$name" "$backup/legacy-$name"
        fi
    done
    printf '✓ %s\n  Backup: %s\n' "$ACTION" "$backup"
}
install_target "$TARGET"
if [ -d "$HOME/Library/Containers/com.blackmagic-design.DaVinciResolveApp" ]; then install_target "$STORE"; fi
if [ "$ACTION" = "Instalar" ]; then
    /usr/bin/osascript -e 'display dialog "Instalado!\n\nNo DaVinci Resolve: Workspace > Scripts > Edit > Titan Studio.\nReabra o plugin para carregar esta versão." with title "Titan Titles Studio" buttons {"Concluir"} default button "Concluir"'
else
    /usr/bin/osascript -e 'display dialog "Titan removido.\n\nBackup preservado; outros plugins foram mantidos." with title "Titan Titles Studio" buttons {"Concluir"} default button "Concluir"'
fi
