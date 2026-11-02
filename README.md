# CAE · Painel 3D

Painel 3D (three.js) do Centro de Aquisições Específicas (CAE, UASG 120195): quartel com o Comando e as divisões de Contrato, Obtenção e Administrativa. Clique em cada prédio para ver as informações da divisão.

- Página única: `index.html` (sem build)
- Dados de exemplo; integração futura com Tesouro Gerencial, SIAFI e Comprasnet/PNCP

Desenvolvido por **DomDevLabs** · v1.14.7

## Instalar no celular

- **Android (Chrome):** toque em **Instalar app** no topo do painel, ou no menu ⋮ > *Instalar app*.
- **iPhone (Safari):** toque em **Instalar app** e siga o passo a passo: Compartilhar > *Adicionar à Tela de Início*.

O ícone é o brasão do CAE e o app abre em tela cheia com o nome **CAE Dashboard**.

## Banco de dados (leitura ao vivo)

O site lê a planilha pública “BD Site Dashboad CAE” (abas Execução e NE) direto do navegador:
ao abrir, a cada 10 minutos e quando o botão **Atualizar** (topo da tela) é clicado. Assim, quando a planilha muda, o site acompanha sem novo deploy.
Se o Google não responder, o site usa a cópia de reserva embutida no `index.html` e avisa na tela.

Para regravar a cópia de reserva: Actions › “Atualizar snapshot de reserva” › Run workflow (ou `node tools/gerar_snapshot.mjs --fetch --bump`).
