# Revisão de pontuação — utility-v2

Correção de 12/10/2026, aplicada a todos os perfis e às builds de personagens.

- Crítico tem peso zero em todos os perfis gerais. A opção específica de crítico continua disponível. Builds só atribuem peso a crítico quando uma regra identifica um trait relacionado, com evidência visível.
- HP máximo, recuperação de HP e recarga de esquiva são categorias distintas.
- Dano causado e atributo ATK são separados; redução de dano e atributo DEF também.
- Captura de tesouro não inclui velocidade de movimento.
- Existem objetivos separados para cura, esquiva e movimento.
- Gatilhos de crítico e aplicação de status em inimigos começam desativados. Configure as condições quando seu personagem justificar essa sinergia.
- Buffs não acumuláveis do mesmo canal usam o maior valor também entre tags e efeitos únicos.
- Trocar o objetivo invalida resultados e cancela uma busca anterior, evitando mostrar o conjunto de outro cenário.
- Preferências padrão antigas são migradas; pesos personalizados são preservados com as categorias antes combinadas distribuídas explicitamente. Conjuntos salvos permanecem disponíveis.

A busca continua exaustiva para o objetivo selecionado. Seus pesos são heurísticos, não uma simulação de combate nem garantia de melhor set universal. Skills ainda distinguem recarga instantânea e velocidade de recarga na decomposição; a soma ponderada não é redução final de cooldown. Atributos adicionais só entram quando selecionados. O objetivo de HP máximo pode favorecer medalhas antigas com HP em seu efeito único; isso não as torna a melhor build geral.

Validação: regressões para separação de categorias, crítico nos perfis gerais, condições explícitas e acúmulo de buffs; comparação da busca NumPy com avaliação escalar para todos os perfis; auditoria das 248.865 duplas do catálogo em cada perfil; recálculo das builds de dois e três slots para os 433 registros de personagens.
