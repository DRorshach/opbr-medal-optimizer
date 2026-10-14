# Revisão de pontuação — utility-v2

## Defender — revisão de 14/10/2026 (utility-v3-defender)

O perfil Defender agora representa defesa do próprio tesouro sem aliados próximos. Redução de dano tem peso 3, cura 2, recarga das skills 1, esquiva 0,4 e captura 0. Os pesos são escolhas do modelo, não coeficientes oficiais do jogo. Efeitos de estar no próprio tesouro ou sem aliados próximos recebem fator 1; captura, área inimiga e aliados próximos recebem 0. Proteção dependente de status no inimigo exige configuração explícita. Outras condições mantêm 0,5 e eventos 0,25. Ajustes manuais de condições têm precedência.

Character Builds calcula os cenários Defender e os demais separadamente, para não compartilhar fatores incompatíveis na avaliação em lote. Todos os sets foram recalculados nos catálogos completo e sem eventos. A interface exibe a hipótese do cenário e mantém bônus completos separados da estimativa do ranking. O perfil não presume que todo defensor esteja sempre sozinho nem modela automaticamente mudanças de classe.

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

Sustentação por classe é uma opção separada de HP máximo + recuperação, que mantém seus pesos anteriores. A nova opção combina cura com as prioridades da classe, incluindo proteção e recarga de skills. Para Defender, assume defesa de posição: efeitos ao capturar tesouro ou no tesouro inimigo recebem fator zero por padrão. As condições podem ser ajustadas explicitamente. HP adicional deve ser configurado nos traits; o resultado continua sendo uma estimativa para o cenário selecionado.
