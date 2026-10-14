#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
VERSION="$(tr -d '\r\n' < "$ROOT/VERSION")"
[ "$(uname -s)" = Darwin ] || { echo 'Este build requer macOS.' >&2; exit 1; }
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/scripts/payload/icons" "$STAGE/ui" "$ROOT/dist"
cp "$ROOT/tools/macos/postinstall" "$STAGE/scripts/postinstall"
cp "$ROOT/tools/macos/install_engine.sh" "$STAGE/scripts/install_engine.sh"
cp "$ROOT/VERSION" "$STAGE/scripts/VERSION"
cp "$ROOT/src/Titan Titles Studio.py" "$ROOT/src/titan_update.py" "$STAGE/scripts/payload/"
cp "$ROOT/src/icons/"* "$STAGE/scripts/payload/icons/"
chmod 755 "$STAGE/scripts/postinstall" "$STAGE/scripts/install_engine.sh"
cp "$ROOT/src/icons/titan_word.png" "$STAGE/ui/titan_word.png"
cat > "$STAGE/ui/Welcome.html" <<'HTML'
<html><meta charset="utf-8"><style>body{font:14px -apple-system;color:#233047;padding:12px}h1{font-size:27px;color:#176d9b}strong{color:#176d9b}</style><img src="titan_word.png" width="185"><h1>Titan Titles Studio</h1><p>Layouts, tipografia e movimento para DaVinci Resolve.</p><p><strong>Titânio & Azul Elétrico · @rangelmaker_</strong></p><p>Este instalador configura o Titan para a conta conectada ao Mac, substitui versões anteriores e guarda um backup fora do menu de scripts.</p><p>Feche a janela do Titan antes de continuar. Outros plugins e títulos já criados nos projetos serão preservados.</p></html>
HTML
cat > "$STAGE/ui/Conclusion.html" <<'HTML'
<html><meta charset="utf-8"><style>body{font:14px -apple-system;color:#233047;padding:12px}h1{color:#176d9b}</style><h1>Seu próximo título começa aqui.</h1><p>Reabra o DaVinci Resolve.</p><p><strong>Workspace → Scripts → Edit → Titan Studio</strong></p><p>O menu terá apenas uma entrada Titan. Recursos e backups ficam na pasta Fusion, fora de Scripts.</p><p>@rangelmaker_ · Titan Titles Studio</p></html>
HTML
cat > "$STAGE/Distribution.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
 <title>Titan Titles Studio</title>
 <organization>com.rangelmaker.titantitlesstudio</organization>
 <options customize="never" require-scripts="false" hostArchitectures="arm64,x86_64"/>
 <domains enable_anywhere="false" enable_currentUserHome="false" enable_localSystem="true"/>
 <welcome file="Welcome.html" mime-type="text/html"/>
 <conclusion file="Conclusion.html" mime-type="text/html"/>
 <choices-outline><line choice="titan"/></choices-outline>
 <choice id="titan" title="Titan Titles Studio $VERSION" visible="false"><pkg-ref id="com.rangelmaker.titantitlesstudio"/></choice>
 <pkg-ref id="com.rangelmaker.titantitlesstudio" version="$VERSION" auth="Root">TitanComponent.pkg</pkg-ref>
</installer-gui-script>
XML
pkgbuild --nopayload --scripts "$STAGE/scripts" --identifier com.rangelmaker.titantitlesstudio --version "$VERSION" "$STAGE/TitanComponent.pkg"
ARGS=()
if [ -n "${TITAN_INSTALLER_IDENTITY:-}" ]; then ARGS+=(--sign "$TITAN_INSTALLER_IDENTITY" --timestamp); fi
productbuild --distribution "$STAGE/Distribution.xml" --resources "$STAGE/ui" --package-path "$STAGE" "${ARGS[@]}" "$ROOT/dist/Titan-Titles-Studio-Mac-$VERSION.pkg"
if [ -n "${TITAN_NOTARY_PROFILE:-}" ]; then
    [ -n "${TITAN_INSTALLER_IDENTITY:-}" ] || { echo 'Notarização exige assinatura Developer ID Installer.' >&2; exit 1; }
    xcrun notarytool submit "$ROOT/dist/Titan-Titles-Studio-Mac-$VERSION.pkg" --keychain-profile "$TITAN_NOTARY_PROFILE" --wait
    xcrun stapler staple "$ROOT/dist/Titan-Titles-Studio-Mac-$VERSION.pkg"
fi
pkgutil --check-signature "$ROOT/dist/Titan-Titles-Studio-Mac-$VERSION.pkg" || true
echo "Built $ROOT/dist/Titan-Titles-Studio-Mac-$VERSION.pkg"
