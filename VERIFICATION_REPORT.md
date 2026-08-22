# Relatório de verificação pré-deploy

## Validado nesta entrega

- Sintaxe de todos os arquivos Python (`compileall` / `py_compile`).
- Sintaxe de todos os JavaScripts com `node --check`.
- JSON do `vercel.json`.
- Referências `{% url %}` dos templates contra as rotas Django declaradas.
- Ausência de Access Token e Webhook Secret reais nos arquivos preparados para Git.
- Configuração do Payment Brick limitada a Pix e cartão de crédito, com até 6 parcelas.
- Backend usa o total persistido no pedido em vez de aceitar um total enviado pelo navegador.
- Uso de chave de idempotência por tentativa de compra.
- Persistência do `external_reference` e conferência de valor antes de alterar o status do pedido.
- Leitura do QR Code Pix (`qr_code_base64`) e Pix Copia e Cola (`qr_code`) retornados pelo Mercado Pago.
- Webhook de pagamentos com suporte à validação `x-signature` quando `MERCADOPAGO_WEBHOOK_SECRET` estiver configurado.
- Endpoint `/healthz/` para verificar banco e presença da configuração Mercado Pago em produção.
- Banco SQLite bloqueado na Vercel; produção exige PostgreSQL persistente.
- Arquivos de segredo e banco local ignorados pelo Git/Vercel.

## Testes automatizados incluídos

`store/tests.py` inclui testes para:

- mapeamento de status do Mercado Pago;
- armazenamento dos dados de QR Code Pix;
- proteção contra alteração do valor pelo navegador;
- envio de `X-Idempotency-Key`;
- rejeição de resposta com valor diferente do pedido;
- funcionamento do endpoint de health check sem nickname.

`.github/workflows/ci.yml` executa `manage.py check`, valida migrations e roda os testes em cada push/pull request.

## Limitação desta verificação

Não foi feita uma cobrança real nem criada uma cobrança Pix real nesta sessão. Isso exigiria o Access Token privado da sua conta e uma transação no ambiente Mercado Pago. O Access Token não deve ser enviado no chat nem commitado no GitHub.

A validação final deve ser feita no primeiro deploy usando credenciais de teste no ambiente da Vercel. Depois de confirmar cartão, geração do QR Pix, consulta de status e webhook, troque as credenciais para produção e faça uma compra real de baixo valor antes de abrir a loja ao público.
