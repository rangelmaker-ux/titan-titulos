Titan Titles Studio v3.3.10

Corrige a criação da faixa de efeitos que desaparecia logo depois: o corte de áudio passado ao AppendToTimeline estava um frame curto. A validação detectava essa diferença e desfazia a inserção. Agora o limite de corte corresponde ao intervalo real devolvido pelo Resolve.

As janelas dos sons também convertem a duração da animação para os frames da timeline quando o template Text+ tem FPS diferente. A identificação e os sons por animação continuam funcionando no Windows e no Mac.

Validação dentro do DaVinci Resolve 21.1.1 no Windows: inserção e substituição de sons em timelines de 24, 29.97 e 60 fps, com início/fim exatos, marcadores e ausência de duplicatas. Projetos temporários removidos e projeto original restaurado. Testes automatizados e instalação nativa no macOS também fazem parte da publicação; a reprodução dentro do Resolve no Mac deve ser conferida no computador do usuário.
