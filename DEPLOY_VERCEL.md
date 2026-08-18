# Deploy do Pixelmon Adventures na Vercel

Este projeto está preparado para Django 6 + Vercel + PostgreSQL persistente + Mercado Pago Payment Brick.

## 1. Antes de enviar para o GitHub

Não envie `.env`, `db.sqlite3`, Access Token ou chave secreta do webhook. O `.gitignore` já bloqueia esses arquivos.

Confirme que o repositório contém, entre outros:

- `manage.py`
- `requirements.txt`
- `pyproject.toml`
- `vercel.json`
- `store/migrations/`
- `.env.example`

## 2. Banco de dados obrigatório em produção

A Vercel executa o Django em ambiente serverless; não use o SQLite local como banco de produção. Conecte um PostgreSQL persistente pelo Marketplace da Vercel (por exemplo Neon). A integração deve disponibilizar `DATABASE_URL` no projeto.

O deploy foi configurado para falhar de propósito se estiver na Vercel sem `DATABASE_URL`, evitando perder pedidos e sessões em um banco efêmero.

## 3. Variáveis de ambiente na Vercel

Configure em **Project > Settings > Environment Variables**:

```env
DJANGO_SECRET_KEY=gere-uma-chave-secreta-grande
DEBUG=False
DATABASE_URL=fornecida-pelo-postgresql
SITE_URL=https://SEU-DOMINIO
DJANGO_ALLOWED_HOSTS=SEU-DOMINIO
CSRF_TRUSTED_ORIGINS=https://SEU-DOMINIO
MERCADOPAGO_PUBLIC_KEY=SUA_PUBLIC_KEY
MERCADOPAGO_ACCESS_TOKEN=SEU_ACCESS_TOKEN
MERCADOPAGO_WEBHOOK_SECRET=SUA_CHAVE_SECRETA_DO_WEBHOOK
MERCADOPAGO_NOTIFICATION_URL=https://SEU-DOMINIO/pagamentos/mercadopago/webhook/
```

Use credenciais de teste no primeiro deploy de validação. Troque para credenciais de produção apenas quando os testes estiverem concluídos.

## 4. Importar o GitHub na Vercel

1. Crie/push o repositório no GitHub.
2. Na Vercel, escolha **Add New > Project** e importe o repositório.
3. Adicione primeiro o PostgreSQL e as variáveis de ambiente acima.
4. Faça o deploy.

O `vercel.json` executa migrations e `collectstatic` durante o build. O runtime atual da Vercel detecta `manage.py` e o WSGI do Django automaticamente.

## 5. Verificação pós-deploy

Abra:

```text
https://SEU-DOMINIO/healthz/
```

Resposta esperada quando banco e Mercado Pago estiverem configurados:

```json
{
  "ok": true,
  "database": true,
  "mercadopago": true,
  "webhook_signature": true
}
```

Este endpoint nunca exibe credenciais, apenas informa se as configurações existem e se o banco responde.

## 6. Webhook do Mercado Pago

No painel da aplicação Mercado Pago, configure uma notificação Webhook HTTPS apontando para:

```text
https://SEU-DOMINIO/pagamentos/mercadopago/webhook/
```

Para esta integração baseada em `/v1/payments`, selecione notificações de **Payment/Pagamentos**. Copie a chave secreta gerada para `MERCADOPAGO_WEBHOOK_SECRET` na Vercel.

Após alterar uma variável na Vercel, faça um novo deploy para garantir que a versão em produção recebeu a configuração.

## 7. Teste funcional antes de produção

Faça primeiro uma compra com credenciais de teste:

1. Entre com um nickname.
2. Adicione um produto ao carrinho.
3. Abra o checkout.
4. Informe nome, e-mail e CPF de teste compatíveis com o ambiente Mercado Pago.
5. Teste cartão com um cartão de teste oficial.
6. Teste Pix e confirme que a página de pedido mostra QR Code e Pix Copia e Cola.
7. Confira o pedido em `/admin/`.
8. Simule o webhook no painel Mercado Pago e verifique a atualização de status.

Observação: pagamentos criados com credenciais de teste podem não disparar notificações reais como uma cobrança de produção; use também o simulador de Webhooks do painel. A página do pedido possui consulta de status como fallback.

## 8. Produção

Quando tudo estiver validado:

1. Troque `MERCADOPAGO_PUBLIC_KEY` e `MERCADOPAGO_ACCESS_TOKEN` para as credenciais de produção da mesma aplicação/conta.
2. Configure/reconfigure o Webhook de produção e sua chave secreta.
3. Defina `SITE_URL` para o domínio definitivo, por exemplo `https://pixelmonadventures.com.br`.
4. Adicione o domínio no projeto Vercel e atualize `DJANGO_ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`.
5. Faça um pagamento real de baixo valor e confira o crédito na conta Mercado Pago e o status do pedido antes de divulgar a loja.

## 9. Administração e entrega manual

O pagamento aprovado muda o pedido para **Pago**. A entrega continua manual, conforme definido neste momento. No Django Admin existe ação para marcar pedidos pagos como **Entregue**.
