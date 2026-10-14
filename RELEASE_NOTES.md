Titan Titles Studio v3.3.9

Corrige o recebimento de atualizações no macOS: os resultados da busca e do download agora chegam à interface por eventos nativos, funcionando tanto com RunLoop quanto com StepLoop. O About recebe os estados de buscar, baixar e instalar sem depender do ciclo de eventos do Windows.

O atualizador usa os certificados públicos do macOS para validar HTTPS, mesmo quando o Python do Resolve não tem certifi. A verificação de certificados, os limites de download e a validação SHA-256 permanecem ativos.

Se o Mac não consegue receber a correção pelo atualizador antigo, instale Titan-Titles-Studio-Mac-3.3.9.pkg uma vez e reabra o Resolve. As próximas atualizações podem ser buscadas em About > Buscar atualizações.

Validação: fluxo completo de busca, download e instalação com eventos nativos sem StepLoop; certificados nativos sem certifi; instalador e reinstalação no macOS; acesso HTTPS ao GitHub a partir do macOS.
