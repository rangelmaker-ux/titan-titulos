# Publicar atualizações do Titan Titles Studio

O plugin consulta Releases públicas estáveis. Quem tem uma versão anterior a v3.2.0 precisa instalar esta versão uma vez. Commits isolados não disparam atualização dos clientes.

1. Edite `src/Titan Titles Studio.py` e/ou `src/titan_update.py`.
2. Atualize `VERSION` e `APP_VERSION` com a mesma versão maior que a publicada; atualize a versão nos instaladores e `RELEASE_NOTES.md`.
3. Sincronize as cópias do código em `1 - Windows/Arquivos` e `2 - Mac`.
4. Rode `python -m unittest discover -s tests -v` e `python tools/build_release.py`.
5. Faça commit e push para main. Publique uma tag, por exemplo `git tag v3.2.1` e `git push origin v3.2.1`.

O workflow Release testa e monta os pacotes, cria uma Release em rascunho com todos os arquivos e só então a publica. Também pode ser iniciado manualmente em Actions, após atualizar as versões. Não reutilize tags/versões já publicadas.

Para publicação manual, crie uma Release com a tag e anexe todos os arquivos de `dist/`. O atualizador exige `Titan-Titles-Studio-Update.zip` com digest SHA-256 fornecido pelo GitHub.

O repositório deve permanecer público para que clientes consultem e baixem sem token ou conta GitHub. Nunca distribua credenciais junto ao plugin.
