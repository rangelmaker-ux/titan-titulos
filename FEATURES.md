# Titan Titles Studio v3.3.0

## Idioma da interface

No cabeçalho, escolha Português (Brasil), English ou Español. A janela fecha e reabre no idioma escolhido; a preferência fica salva. O idioma da transcrição continua separado em Idioma do áudio. A troca da interface não traduz a fala, os textos existentes ou nomes de fontes.

## Posição

Na aba Títulos > Ajustes, defina X e Y e clique Aplicar posição a todos. Aplica o deslocamento a todos os clipes Text+ da timeline atual, mantendo seus layouts e animações.

Essa operação acontece uma vez. Depois, os sliders voltam a agir somente nos títulos selecionados na lista sob a agulha; sem seleção, no bloco atual. Selecionar uma linha permite ajustar apenas aquela linha, sem alterar os outros títulos que já receberam a posição global.

## About

O cabeçalho contém About. Ali ficam os direitos de criação de RangelMaker_, Instagram @RangelMaker_, Instagram @oWilder.cine e o link da comunidade no Telegram. O crédito foi retirado do cabeçalho e da linha abaixo do logo.

## Efeitos sonoros

Ative Efeitos sonoros em Legendas ou Animações. A preferência é compartilhada entre as abas e fica salva.

- Slide: whoosh curto.
- Bounce: whoosh com clique.
- Blur: whoosh suave.
- Flicker: glitch, com prioridade quando combinado com outros efeitos.
- Shake: glitch de cliques.

Cada entrada e saída recebe um clipe WAV estéreo em faixas Titan SFX. O áudio é ajustado à janela de frames da animação; a saída usa metade da amplitude da entrada. Reaplicar animação ou duração substitui somente os efeitos associados aos títulos alterados. Fontes/layouts mantêm os sons quando a receita da animação não mudou.

Durante a extração para transcrição, faixas que contêm apenas sons marcados como Titan são silenciadas temporariamente e restauradas ao terminar, inclusive se houver falha.

Os cinco áudios foram selecionados do pack fornecido pelo usuário, com autorização de redistribuição confirmada. Só esses trechos curtos foram incluídos, convertidos para PCM estéreo a 48 kHz e normalizados. A seleção foi feita por categoria e análise do sinal; o resultado precisa ser ouvido com as animações no seu projeto.

Arquivos de áudio usados em projetos ficam em Fusion/TitanTitlesStudio-audio, fora de Scripts. Essa pasta é preservada nas reinstalações para não quebrar os links da timeline. Ao transferir projetos para outro computador, inclua esses áudios na coleta de mídia do Resolve.

## Testes

Testes automatizados cobrem construção da interface nos três idiomas, preferências/reinício, posição global seguida de ajuste local, planos de áudio em frames, nível da saída, substituição sem duplicação, preservação de voz, falhas de inserção/exportação e compatibilidade com atualizadores antigos.

Testes com simuladores da API não substituem a validação de som e interação dentro do DaVinci Resolve. A instalação nativa é testada separadamente no runner macOS.
