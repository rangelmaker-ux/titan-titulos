#!/bin/bash
DIR="$( cd "$( dirname """" )" && pwd )"
TARGET="$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit"
TARGET_STORE="$HOME/Library/Containers/com.blackmagic-design.DaVinciResolveApp/Data/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit"
clear
echo "============================================================"
echo "        TITAN TITLES STUDIO v1.0 - @rangelmaker_"
echo "          Instalador Automatico para DaVinci Resolve (macOS)"
echo "============================================================"
echo ""
mkdir -p "$TARGET/icons"
cp -f "$DIR/Titan Titles Studio.py" "$TARGET/"
cp -rf "$DIR/icons/"* "$TARGET/icons/"
if [ -d "$HOME/Library/Containers/com.blackmagic-design.DaVinciResolveApp" ]; then
    mkdir -p "$TARGET_STORE/icons"
    cp -f "$DIR/Titan Titles Studio.py" "$TARGET_STORE/"
    cp -rf "$DIR/icons/"* "$TARGET_STORE/icons/"
fi
echo " [OK] Titan Titles Studio instalado com sucesso no seu Mac!"
echo ""
read -p "Pressione Enter para fechar..."