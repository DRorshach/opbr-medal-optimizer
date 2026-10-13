# OPBR Medal Optimizer — Bounty Lab

Calculadora de medalhas de ONE PIECE Bounty Rush, em português, executada no navegador.

- Catálogo de 706 medalhas, com versões coloridas substituindo douradas equivalentes.
- Calculadora de dois ou três slots, tags e traits adicionais.
- Busca exaustiva com prioridades configuráveis.
- Seleção de 362 personagens e versões, com cinco sets em dois níveis de equipamento, busca, filtro de classe e justificativas do perfil. Registros especiais do cache (`chara_type` diferente de 0), incluindo cópias com skills `???`, ficam fora da seleção; os dados originais são preservados.
- Opção de cinco sets somente com medalhas normais, sem eventos. As imagens coloridas também representam as douradas equivalentes. O ranking é recalculado nesse catálogo e não depende da coleção do visitante.
- Coleção, favoritos e conjuntos salvos somente no navegador de cada visitante.

## Usar

Abra o endereço publicado no GitHub Pages. Não precisa instalar Python. Em Character Builds, busque o personagem e sua versão, escolha nível 80 ou 100 e abra uma sugestão na calculadora.

O primeiro cálculo baixa o ambiente Python/WebAssembly do Pyodide; exige conexão com a internet e pode demorar. A busca de três medalhas avalia mais de 58 milhões de combinações e pode levar vários minutos, especialmente no celular. É possível cancelar. As sugestões prontas de personagens não exigem essa busca.

Exporte sua coleção para manter um backup. Limpar os dados do navegador apaga os favoritos e conjuntos; eles não são sincronizados entre dispositivos.

## Modelo e limitações

Modelo atual: **utility-v2**. Veja [correções de pontuação](SCORING.md). Perfis gerais não priorizam crítico; HP, cura e esquiva são separados, assim como atributos e bônus de combate.

A pontuação é utilidade heurística, não dano final ou chance de vitória. Os efeitos usam fatores condicionais editáveis. Tags dupla/tripla não acumulam entre si. Famílias repetidas são excluídas. Mecânicas de personagens não interpretadas são indicadas nas justificativas; as builds não são recomendações oficiais ou uma simulação completa do jogo.

Os dados foram extraídos de um cache local e não comprovam catálogo completo, disponibilidade atual ou vínculo com uma versão oficial. Descrições originais permanecem em inglês. Imagens e dados do jogo pertencem aos respectivos titulares. Projeto independente, sem afiliação à Bandai Namco.

## Desenvolvimento

Este repositório contém o site estático pronto para publicação. Sirva a pasta com qualquer servidor HTTP, por exemplo `python -m http.server 8000`, e abra `http://localhost:8000`. Abrir o HTML diretamente como arquivo não suporta o worker.

`engine.py` contém o mesmo motor Python da calculadora local. `pages-worker.mjs` executa esse motor em um Web Worker com [Pyodide](https://pyodide.org/en/stable/usage/quickstart.html) 314.0.7; NumPy é carregado quando a busca é solicitada. `pages-api.js` lê JSON estático e grava preferências em localStorage. O site funciona em subpastas do GitHub Pages.

As tabelas públicas, imagens e builds ficam em `data/` e `images/`. Nenhum banco pessoal, cache bruto do jogo, credencial ou caminho do computador integra esta publicação.

## Publicação

Em Settings → Pages, selecione GitHub Actions. O workflow publica a raiz do repositório a cada push em `main` ou execução manual.
