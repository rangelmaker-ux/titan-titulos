# Titan Titles Studio para FilmCraft 1.0.0

Versão para Windows 10/11 x64, validada com FilmCraft 0.7.2. Não requer Python, DaVinci Resolve ou alteração dos arquivos do FilmCraft. É uma janela própria conectada ao editor, não um painel interno.

## Instalar e conectar

1. Execute `Instalar-Titan-FilmCraft-1.0.0.exe` e clique em **Instalar / Atualizar**. O pacote ainda não possui assinatura digital; o Windows pode apresentar um aviso ao executar um aplicativo baixado. Confira o SHA256 fornecido junto do instalador.
2. Salve seu projeto e feche o FilmCraft que estava aberto.
3. Abra o atalho **Titan Titles Studio - FilmCraft** e clique em **Abrir FilmCraft com Titan**.
4. No FilmCraft, abra seu projeto e a sequência desejada. No Titan, clique em **Conectar**.

O atalho abre o Titan; seu botão abre o FilmCraft com a conexão local habilitada. O Titan não fecha nem substitui um FilmCraft aberto sem essa conexão. O canal é restrito a `127.0.0.1:19876`; o FilmCraft oferece esse canal sem autenticação, portanto abra por esse fluxo apenas enquanto usar a integração.

## Gerar

- **Transcrever sequência** exporta o áudio ativo da timeline e executa Whisper localmente. Deixe ativas apenas as faixas de voz. O modelo multilíngue de 488 MB é baixado na primeira utilização e conferido por SHA256. Se o modelo do Titan/Resolve estiver instalado, ele pode ser reaproveitado. A fala não é enviada à nuvem. Português, inglês e espanhol estão disponíveis.
- **Importar SRT** usa os tempos do arquivo. Nos campos de texto, cada linha tem `início | fim | texto`, em segundos. Também é possível escrever títulos manualmente nesse formato.
- **Comum** cria frases estáticas com fonte, tamanho, cor e posição escolhidos.
- **Dinâmica** mantém texto de apoio e anima uma palavra de destaque.
- **Mista** intercala duas legendas comuns com um destaque animado elegível, mantendo pelo menos três segundos entre blocos dinâmicos.
- Use `[palavra]` para definir um destaque manual. A seleção automática escolhe uma palavra de conteúdo longa; é uma heurística, não análise semântica. Com SRT, o tempo da palavra é estimado proporcionalmente; revise quando precisar de precisão. A transcrição usa os tempos retornados pelo Whisper.
- Cada clique em **Gerar títulos** adiciona um novo conjunto. Para substituir, remova o conjunto anterior na timeline antes de gerar novamente.

## Sons e edição

Seis animações: Slide, Bounce, Flicker, Shake, Blur e Motion Blur. Os presets foram recriados com keyframes e efeitos nativos do FilmCraft. Os sons entram somente no início do destaque, duram até 0,3 segundo, usam volume inicial de 35% e respeitam pelo menos dois segundos entre sons.

Na aba de sons, escolha o efeito de cada animação e clique em **Aplicar sons aos destaques existentes**. Isso substitui os sons do Titan, preservando outras faixas. Escolher `none` ou volume zero remove os sons próprios. Título e áudio ficam vinculados para movimentação conjunta.

Os textos, fontes e propriedades continuam editáveis no FilmCraft. A posição do Titan também pode ser aplicada a um título selecionado ou a todos. Mantenha o prefixo `TitanFC[...]` no nome dos clipes para que sejam identificados; editar o conteúdo do texto não altera esse prefixo. Sons próprios usam `TitanSFX[...]`.

## Atualizar ou remover

Execute o novo instalador para substituir a versão anterior. No About, **Buscar atualizações** consulta somente as versões FilmCraft no GitHub e abre o download quando existe uma versão mais recente. Depois execute o instalador baixado. Esta versão usa um canal separado do atualizador do Resolve. O instalador também oferece **Remover versão instalada** quando já existe uma instalação. Projetos, configurações e WAVs gerados são preservados para não deixar mídia offline em projetos existentes.

## Limites desta versão

O FilmCraft está em alpha e sua API pode mudar. Esta entrega é Windows x64; não inclui instalador Mac. Não contém todos os layouts especiais do Fusion. Os presets são equivalentes nativos, não os mesmos nós do DaVinci. Avalie a tipografia e o ritmo no seu vídeo antes de usar em produção.

Criação: RangelMaker_. Instagram: @RangelMaker_ e @oWilder.cine. Comunidade: https://t.me/+y2SoJmZgRTwyOTI5

Motor: whisper.cpp (MIT), versão 1.9.4 unicode-r2; licença junto do instalador. Modelo: https://huggingface.co/ggerganov/whisper.cpp, pesos OpenAI Whisper. Interface: Python/Tk e Pillow. Efeitos sonoros redistribuídos com autorização do titular confirmada pelo responsável pelo Titan.
