# Vitalia — Portal do Doador

Portal que conecta mães doadoras a bancos de leite humano no Brasil, facilitando a doação de
leite materno excedente para bebês prematuros internados em UTIs neonatais da rede pública.
Construído com FastAPI + SQLite + Jinja2, sem dependência de frontend framework.

## Como rodar

```bash
pip install -r requirements.txt
python start.py
```

O servidor sobe em `http://127.0.0.1:8000` (e também no IP da rede local, para testar pelo
celular). O banco SQLite (`data/blhs.db`) já vem com os bancos de leite carregados; as demais
tabelas (doadoras, campanhas, eventos, etc.) são criadas automaticamente na primeira execução.

### Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `ANTHROPIC_API_KEY` | Não | Chave da API da Anthropic para o chatbot da página inicial. Sem ela, o chat responde com um aviso amigável em vez de falhar. Gere uma em [console.anthropic.com](https://console.anthropic.com). |

### Login do administrador

O painel (`/admin/dashboard`, `/admin/campanhas`) exige login em `/admin/login`.

- Usuário: `Adm`
- Senha: `Adm123`

Credenciais e a chave de sessão estão fixas em `app/config.py` para fins de desenvolvimento —
troque antes de qualquer deploy real.

## Atualizações recentes

- **Correção do dropdown de Estado** no cadastro do Portal do Doador: as opções agora são
  renderizadas pelo servidor (como nas demais páginas) em vez de depender de uma chamada
  JavaScript que podia falhar silenciosamente e deixar o campo vazio.
- **Login de administrador**: as rotas `/admin/campanhas` e `/admin/dashboard`, que antes
  ficavam abertas para qualquer visitante, agora exigem autenticação via sessão. A antiga página
  independente "Seja uma doadora" foi removida — o cadastro acontece só pelo fluxo guiado da
  página inicial.
- **Dashboard reformulado**: cards de KPI (cadastros, agendamentos, taxa de conversão, avaliação
  média) com variação real vs. mês anterior, funil de conversão em 3 estágios coloridos, lista de
  cadastros por estado, avaliação das doadoras com distribuição por estrela, gráfico de cadastros
  nos últimos 14 dias e gráfico de horário de acesso em colunas. Rótulos de eventos e perguntas do
  quiz foram traduzidos para texto legível (antes apareciam como nomes de variável, ex.
  `quiz_completed`).
- **Chatbot no Portal do Doador**: assistente flutuante que responde dúvidas sobre o Vitalia e
  sobre doação de leite materno, usando a API da Claude (Anthropic) com um prompt restrito ao
  conteúdo do site — perguntas fora desse escopo são recusadas explicitamente. Requer
  `ANTHROPIC_API_KEY` configurada (ver acima).
- Removido o placeholder "Vídeo em produção" do passo de vídeo do wizard.
- Diversos ajustes de layout: rodapé sempre fixo na base da página (mesmo em páginas curtas),
  botão do chat reposicionado para não sobrepor o rodapé.
