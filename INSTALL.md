# Titan Titles Studio

Identidade Titânio & Azul Elétrico • @rangelmaker_

Extraia o ZIP inteiro antes de instalar. Feche a janela do Titan no Resolve.

## Windows

Abra `Instalar_Windows.bat`. O instalador permite instalar/atualizar, remover a versão anterior antes de instalar ou remover o Titan. Não requer administrador.

## Mac

Abra `Instalar_no_Mac.command`. Escolha Instalar ou Remover; ao instalar, escolha manter os arquivos ou remover a versão anterior. Se o macOS não permitir abrir, use Abrir pelo menu de contexto ou consulte Privacidade e Segurança. Se o ZIP perder a permissão executável, rode `bash ` seguido do caminho do instalador no Terminal (arraste o arquivo para preencher o caminho).

O instalador usa diálogos nativos do macOS e um cabeçalho Titânio/Azul no Terminal. Os diálogos seguem a aparência do sistema.

## Abrir o plugin

No DaVinci Resolve: Workspace > Scripts > Edit > Titan Titles Studio. Se não aparecer, reinicie o Resolve.

## Atualizações

Ao abrir, o Titan consulta a última versão estável no GitHub. Sem internet, continua funcionando. Quando surgir o aviso, clique Baixar e depois Instalar. A instalação guarda um backup e fecha a janela; reabra o Titan para carregar a nova versão.

A consulta não exige conta GitHub. O repositório e as Releases devem permanecer públicos. Somente Releases estáveis com pacote de atualização válido são distribuídas; commits e versões de teste não atualizam os clientes.

No modo de dispatcher do Resolve sem StepLoop, use o botão de atualizar a leitura da timeline para exibir o resultado da consulta e o progresso do download.

## Remoção e backup

Os instaladores removem apenas `Titan Titles Studio.py` e a pasta exclusiva `TitanTitlesStudio`. Não apagam a pasta compartilhada `icons` da instalação antiga, porque outros scripts podem utilizá-la. Backups ficam em `TitanTitlesStudio-backups`, junto à pasta de scripts Edit. Projetos e títulos já criados na timeline são preservados.

Para restaurar: feche o Titan; copie `Titan Titles Studio.py` do backup para Edit e a pasta `TitanTitlesStudio` do backup para Edit. Em backups criados pelo atualizador, copie `titan_update.py` e `icons` para `Edit/TitanTitlesStudio`.

Esta distribuição não é assinada/notarizada. Validação de instalação e interação no Resolve do Mac deve ser realizada em um Mac antes de anunciar compatibilidade comercial completa.
