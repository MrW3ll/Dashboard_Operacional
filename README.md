📊 SECAD | Monitor Operacional

Dashboard operacional em tempo real para monitoramento de vendas e atendimentos do call center SECAD.

Tecnologias
  Python · Streamlit · Plotly · SQLAlchemy · PostgreSQL

Estrutura do projeto
  secad_v2/
  ├── app.py          # Aplicação principal
  ├── queries.py      # Queries SQL
  ├── .env            # Credenciais do banco (NÃO sobe pro GitHub)
  ├── .gitignore
  └── README.md

Como rodar localmente

  1. Clone o repositório
  bashgit clone https://github.com/seu-usuario/secad-monitor.git
  cd secad-monitor
  2. Instale as dependências
  bashpip install streamlit plotly sqlalchemy psycopg2-binary pandas python-dotenv streamlit-autorefresh
  3. Configure as credenciais
  Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:
  DB_USER=seu_usuario
  DB_PASSWORD=sua_senha
  DB_HOST=seu_host
  DB_PORT=5432
  DB_NAME=nome_do_banco
  4. Rode o app
  bashstreamlit run app.py
  
Funcionalidades

  Atualização automática a cada 5 minutos
  KPIs de performance mensal (vendas, receita, ticket médio, taxas)
  Resultado operacional do dia
  Comparativo vs média histórica dos últimos 5 meses
  Gráficos de venda e atendimento por área  
