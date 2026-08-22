# Pixelmon Adventures Store

Loja Django do servidor Pixelmon Adventures, com gateway por nickname, catálogo de VIPs, carrinho, equipe, páginas institucionais e checkout transparente Mercado Pago.

## Stack

- Python 3.12+
- Django 6
- Mercado Pago Payment Brick
- Pix e cartão de crédito (máximo de 6 parcelas)
- SQLite somente para desenvolvimento local
- PostgreSQL em produção
- WhiteNoise para assets estáticos
- Vercel para deploy serverless

## Desenvolvimento local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`.

Para testar pagamentos, preencha no `.env` uma Public Key e um Access Token pertencentes ao mesmo ambiente Mercado Pago. Nunca envie o Access Token para o GitHub.

## Checkout Mercado Pago

O frontend usa o Payment Brick oficial. Os dados sensíveis de cartão são tokenizados pelo SDK do Mercado Pago no navegador; o backend recebe o token e cria o pagamento pela API `/v1/payments`.

O total enviado ao Mercado Pago vem do pedido persistido no backend, e não do valor recebido do navegador. Cada tentativa possui uma chave de idempotência própria. Para Pix, o QR Code e o Pix Copia e Cola retornados pelo Mercado Pago são armazenados no pedido e exibidos na página de status.

O webhook está em:

```text
/pagamentos/mercadopago/webhook/
```

A entrega dos itens é manual neste momento. Um pagamento aprovado altera o pedido para `Pago`; no Django Admin existe uma ação para marcar a entrega como concluída.

## Deploy Vercel

Leia [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) antes de importar o repositório na Vercel.

A produção exige `DATABASE_URL`: o projeto recusa iniciar na Vercel usando SQLite para evitar perda de pedidos/sessões.

Após o deploy, use `/healthz/` para confirmar conexão com banco e presença das configurações de pagamento sem expor segredos.

## Segurança

- `.env` e `db.sqlite3` ficam fora do Git.
- Access Token e Webhook Secret são somente variáveis de ambiente.
- O CPF completo não é persistido; o banco guarda apenas os quatro últimos dígitos.
- Webhooks podem ser validados pela assinatura secreta `x-signature`.
- O backend confere `external_reference` e valor antes de atualizar o pedido.
