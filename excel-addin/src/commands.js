/**
 * Organizer App — Ações da Faixa de Opções (Ribbon Commands)
 */

Office.onReady(() => {
  // Inicialização de comandos globais
});

function action(event) {
  // Ação disparada por botões do ribbon
  event.completed();
}

// Registra a função no namespace global do Office
if (typeof Office !== "undefined" && Office.actions) {
  Office.actions.associate("action", action);
}
