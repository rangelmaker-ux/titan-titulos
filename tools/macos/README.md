# Instalador nativo macOS

O pacote `.pkg` abre no Instalador do macOS, que pede autorização de administrador. Não depende de Python, execução de `.command` pelo Finder ou de cópia manual.

Instala na conta conectada ao Mac. A versão anterior e os scripts antigos conhecidos do Titan são retirados do menu e guardados em Fusion/TitanTitlesStudio-backups. Outros plugins não são selecionados pela limpeza. O pacote pode ser executado novamente; mantém apenas Titan Studio no menu. A instalação tradicional e a edição App Store, quando o container existe, são atendidas.

## Build

Em macOS: `bash tools/macos/build_pkg.sh`. O workflow Mac Installer monta e testa o pacote em um runner macOS; o arquivo fica nos artefatos da execução. O workflow Release também inclui o `.pkg` nas próximas Releases.

## Assinatura e aprovação Apple

Um `.pkg` sem assinatura ainda pode exigir Ajustes do Sistema > Privacidade e Segurança > Abrir Mesmo, quando o sistema permitir. Mudar a extensão ou o script não elimina o Gatekeeper. Nunca desative a proteção do macOS como requisito de instalação.

Para distribuição comercial, use certificado Developer ID Installer no chaveiro de um Mac e defina `TITAN_INSTALLER_IDENTITY` com a identidade. Para notarizar, configure um perfil com `xcrun notarytool store-credentials` e defina `TITAN_NOTARY_PROFILE` com o nome desse perfil. O build assina, aguarda a aprovação da Apple e anexa o ticket ao pacote. Não coloque credenciais no repositório.

## Condições de erro

- Sem usuário conectado: entrar na conta e repetir a instalação.
- Instalação em outro volume: escolher o disco de inicialização.
- Pacote incompleto ou caminhos redirecionados: instalação interrompida.
- Falha durante a substituição: arquivos anteriores restaurados.
- Restrições corporativas ou de Privacidade do macOS: podem exigir intervenção do administrador.
- Bloqueio de software não identificado: autorização do macOS ou assinatura/notarização. Não se declara um pacote aprovado pela Apple sem essa etapa.
