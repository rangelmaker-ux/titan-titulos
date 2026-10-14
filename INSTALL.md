# Titan Titles Studio

Identidade Titânio & Azul Elétrico • @rangelmaker_

Extraia o ZIP inteiro antes de instalar. Feche a janela do Titan no Resolve.

## Windows

Abra `Instalar_Windows.bat`. O instalador permite instalar/atualizar, remover a versão anterior antes de instalar ou remover o Titan. Não requer administrador.

## Mac

Use `Titan-Titles-Studio-Mac-3.3.0.pkg`, abra no Instalador do macOS e siga Continuar > Instalar. Autorize com a senha ou Touch ID quando solicitado. Feche o Titan antes de instalar e reabra o Resolve ao terminar. O instalador limpa os nomes antigos do Titan automaticamente, guardando um backup fora de Scripts.

Este pacote ainda não possui assinatura Developer ID nem notarização. Se o macOS bloquear por desenvolvedor não identificado e oferecer a exceção, autorize em Ajustes do Sistema > Privacidade e Segurança > Abrir Mesmo. Não desative o Gatekeeper. Assinatura/notarização exige certificado Apple; veja tools/macos/README.md.

O `.command` permanece como alternativa para suporte, mas o `.pkg` é a instalação recomendada. Não copie o ZIP inteiro para Scripts/Edit.

## Abrir o plugin

No DaVinci Resolve: Workspace > Scripts > Edit > Titan Studio. Se não aparecer, reinicie o Resolve.

## Atualizações

Ao abrir, o Titan consulta a última versão estável no GitHub. Sem internet, continua funcionando. Quando surgir o aviso, clique Baixar e depois Instalar. A instalação guarda um backup e fecha a janela; reabra o Titan para carregar a nova versão.

A consulta não exige conta GitHub. O repositório e as Releases devem permanecer públicos. Somente Releases estáveis com pacote de atualização válido são distribuídas; commits e versões de teste não atualizam os clientes.

No modo de dispatcher do Resolve sem StepLoop, use o botão de atualizar a leitura da timeline para exibir o resultado da consulta e o progresso do download.

## Remoção e backup

Os instaladores removem apenas `Titan Studio.py` e a pasta exclusiva `TitanTitlesStudio`. Não apagam a pasta compartilhada `icons` da instalação antiga, porque outros scripts podem utilizá-la. Backups ficam em `TitanTitlesStudio-backups`, na pasta Fusion, fora de Scripts. Projetos e títulos já criados na timeline são preservados.

Para restaurar: feche o Titan; copie o script do backup para Edit com o nome `Titan Studio.py` e a pasta `TitanTitlesStudio` para Fusion (fora de Scripts). Em backups criados pelo atualizador, copie `titan_update.py` e `icons` para `Fusion/TitanTitlesStudio`.

Esta distribuição não é assinada/notarizada. Validação de instalação e interação no Resolve do Mac deve ser realizada em um Mac antes de anunciar compatibilidade comercial completa.

Recursos novos: consulte FEATURES.md para idiomas, About, posição global e sons. Não copie módulos auxiliares para Scripts/Edit.
