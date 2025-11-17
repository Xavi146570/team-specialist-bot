1	# Team Specialist Bot - FC Porto, Benfica, Sporting
     2	
     3	Bot especializado em análise dos 3 Grandes de Portugal com **valores MÍNIMOS** (não médias).
     4	
     5	## 🎯 Características
     6	
     7	- ✅ Análise histórica de 5 anos (2019-2024)
     8	- ✅ Cálculo de valores mínimos a 70%, 80%, 90% de confiança
     9	- ✅ Kelly Criterion para dimensionamento de stake
    10	- ✅ 12 triggers (6 pré-jogo + 6 live HT)
    11	- ✅ Monitorização live HT após 30 minutos
    12	- ✅ Relatórios PDF consolidados
    13	- ✅ Alertas Telegram
    14	- ✅ ~3 jogos/semana
    15	
    16	## 📊 Metodologia
    17	
    18	### Valores Mínimos vs Médias
    19	
    20	**Exemplo FC Porto em casa:**
    21	- ❌ Média: 3.2 golos/jogo (enganador)
    22	- ✅ Mínimo 90%: 2 golos (aposta segura)
    23	- ✅ Mínimo 80%: 3 golos (confiança alta)
    24	- ✅ Mínimo 70%: 4 golos (agressivo)
    25	
    26	### Kelly Criterion
    27	
    28	```
    29	f = (bp - q) / b
    30	
    31	f = fração do bankroll
    32	b = odds - 1
    33	p = probabilidade (dos dados históricos mínimos)
    34	q = 1 - p
    35	```
    36	
    37	## 🔧 Instalação
    38	
    39	### 1. Clone do GitHub
    40	
    41	```bash
    42	git clone https://github.com/seu-usuario/team-specialist-bot.git
    43	cd team-specialist-bot
    44	```
    45	
    46	### 2. Configurar variáveis de ambiente
    47	
    48	```bash
    49	cp .env.example .env
    50	```
    51	
    52	Editar `.env` com:
    53	- API-Football key
    54	- Supabase URL + Service Key
    55	- Telegram Bot Token + Chat ID
    56	
    57	### 3. Deploy no Railway
    58	
    59	1. Criar novo projeto no Railway
    60	2. Conectar repositório GitHub
    61	3. Adicionar variáveis de ambiente
    62	4. Deploy automático
    63	
    64	## 📁 Estrutura
    65	
    66	```
    67	team_specialist_bot/
    68	├── main.py                          # Entry point
    69	├── modules/
    70	│   ├── data_collector.py           # API-Football integration
    71	│   ├── minimum_analyzer.py         # Cálculo de mínimos 70%/80%/90%
    72	│   ├── trigger_detector.py         # Deteção dos 12 triggers
    73	│   ├── kelly_calculator.py         # Kelly Criterion
    74	│   ├── live_monitor.py             # Monitorização HT 30-45min
    75	│   ├── pdf_generator.py            # Relatórios PDF
    76	│   ├── telegram_notifier.py        # Alertas Telegram
    77	│   └── supabase_client.py          # Database integration
    78	├── requirements.txt
    79	├── Dockerfile
    80	└── README.md
    81	```
    82	
    83	## 🎲 Triggers Implementados
    84	
    85	### Pré-Jogo (6)
    86	1. `vs_bottom5_home` - Casa vs equipas 16º-18º
    87	2. `vs_top3_home` - Casa vs outros Big 3
    88	3. `post_loss_home` - Casa após derrota
    89	4. `classico` - Porto vs Benfica/Sporting
    90	5. `champions_week` - Semana com Champions
    91	6. `vs_bottom5_away` - Fora vs equipas fracas
    92	
    93	### Live HT (6)
    94	7. `ht_0x0_after_30min_home` - 0-0 aos 30-45min em casa
    95	8. `ht_1x0_winning_home` - 1-0 ao intervalo em casa
    96	9. `ht_losing_home` - A perder ao intervalo em casa
    97	10. `ht_drawing_away` - Empate ao intervalo fora
    98	11. `ht_0x0_after_30min_away` - 0-0 aos 30-45min fora
    99	12. `second_half_momentum` - Força na 2ª parte
   100	
   101	## ⏰ Agendamento
   102	
   103	- **Análise completa**: Domingos às 02:00 (semanal)
   104	- **Check próximos jogos**: Diariamente às 10:00 e 18:00
   105	- **Monitorização live**: A cada 5 minutos
   106	
   107	## 📈 Output
   108	
   109	### 1. Database (Supabase)
   110	- `team_specialist_analysis` - Análises históricas
   111	- `team_trading_plans` - Planos de trading por jogo
   112	
   113	### 2. Telegram
   114	- Alertas pré-jogo com plano Kelly
   115	- Alertas live HT com triggers ativos
   116	- Relatório PDF semanal
   117	
   118	### 3. PDF Report
   119	- Análise consolidada das 3 equipas
   120	- Tabelas de valores mínimos
   121	- Triggers ativos
   122	- Histórico 5 anos
   123	
   124	## 🔐 Segurança
   125	
   126	- Service key do Supabase (não usar anon key)
   127	- RLS policies limitam acesso a users premium
   128	- Variáveis de ambiente no Railway (não commit no Git)
   129	
   130	## 📝 Logs
   131	
   132	```bash
   133	# Railway logs
   134	railway logs
   135	
   136	# Local testing
   137	python main.py
   138	```
   139	
   140	## 🚀 Próximos Passos
   141	
   142	1. ✅ Deploy no Railway
   143	2. ⏳ Gerar análise inicial (5 anos × 3 equipas)
   144	3. ⏳ Criar página frontend `/team-specialist`
   145	4. ⏳ Integração com odds ao vivo
   146	5. ⏳ Champions League calendar integration
   147	
   148	## 💡 Notas
   149	
   150	- Bot corre 24/7 no Railway
   151	- Análise semanal automática aos domingos
   152	- Alertas apenas para triggers com confiança alta
   153	- Kelly limitado a 25% do bankroll (risk management)
   154	
   155	---
   156	
   157	**Desenvolvido para análise profissional dos 3 Grandes de Portugal** 🇵🇹
