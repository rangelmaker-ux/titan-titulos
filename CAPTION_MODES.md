# Legendas com foco no destaque

Na aba LEGENDAS, escolha **Modo de legenda** antes de gerar:

- **Comum**: frases estáticas, sem animação ou efeitos sonoros. Usa fonte, estilo, cor e caixa alta da linha Principal. O tamanho é fixo entre os blocos e pode ser definido em Tamanho da comum; a largura orienta a quebra de linhas.
- **Dinâmica**: destaca uma palavra de conteúdo por bloco elegível. Só ela recebe animação. Os textos de apoio usam a fonte Apoio e permanecem estáticos.
- **Mista**: começa com dois blocos comuns e intercala um bloco dinâmico quando há destaque elegível e espaço no ritmo. Usa a fonte Apoio nos trechos comuns e a fonte Principal nos destaques.

Mista é a configuração inicial. O texto completo e os tempos reconhecidos da fala são preservados. A escolha automática de destaques usa as regras linguísticas existentes do plugin, não uma análise semântica por IA. Os blocos sem palavra elegível permanecem comuns.

## Um acento sonoro

Somente a entrada do destaque recebe um som, mesmo quando a animação combina efeitos. A saída, as palavras de apoio e as legendas comuns ficam sem som.

- Acentos de até 0,4 s; volume inicial de 35%, ajustável no menu Sons por animação.
- Intervalo mínimo de 2 s entre acentos. Na Mista, o planejamento separa os blocos dinâmicos por pelo menos 3 s e dois blocos comuns.
- A geração automática prefere Slide e Blur suaves, com movimento pequeno e entrada de cerca de 0,3 s. Os seis estilos continuam disponíveis para escolhas manuais.
- O áudio conserva o tom original: o arquivo é cortado ou completado com silêncio, com fades, em vez de acelerado.

O volume é uma configuração inicial, não uma medição da voz. Ajuste-o ao ouvir a mixagem.

## Ajustar um projeto existente

Em Sons por animação, use **Focar animações e sons nos destaques** para tornar estáticos os textos de apoio do Titan e concentrar os sons no principal. A identificação de títulos antigos usa o tamanho do texto dentro do bloco; revise se o projeto foi muito alterado.

Na aba TÍTULOS, selecione um único texto e use **Definir como destaque** ou **Usar como apoio**. O papel fica salvo no clipe. Ao marcar outro destaque no mesmo bloco, os demais passam a apoio.

**Aplicar todas as animações** reaplica o mapeamento sonoro aos destaques e remove sons antigos de apoio/saída que pertencem ao Titan. Faixas de voz e outros áudios sem marcadores do Titan são preservados. Faixas vazias usadas pelos efeitos antigos são retiradas.

Trocar o modo afeta a próxima geração de legendas; não reconstrói automaticamente as palavras e layouts de uma timeline já editada.

## Referências usadas no desenho

- [Descript: texto legível e destaques sem excesso](https://www.descript.com/blog/article/video-beginners-guide-to-text).
- [Adobe: animação para guiar o olhar e hierarquia visual](https://www.adobe.com/learn/after-effects/web/creating-animating-text).
- [iZotope: manter a voz audível acima dos efeitos](https://www.izotope.com/community/blog/mixing-audio-for-video-part-3-tools-of-the-trade).

Os intervalos, volumes e cadência acima são decisões iniciais deste plugin para teste criativo; não são limites exigidos pelas referências.
