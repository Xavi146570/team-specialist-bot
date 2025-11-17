1	"""
     2	Team Specialist Bot - FC Porto, Benfica, Sporting Analysis
     3	Analyzes 3 biggest Portuguese teams with MINIMUM values (not averages)
     4	Uses Kelly Criterion for stake sizing
     5	Monitors live HT triggers after 30 minutes
     6	"""
     7	
     8	import os
     9	import logging
    10	from datetime import datetime, timedelta
    11	from apscheduler.scheduler import Scheduler
    12	
    13	from modules.data_collector import DataCollector
    14	from modules.minimum_analyzer import MinimumAnalyzer
    15	from modules.trigger_detector import TriggerDetector
    16	from modules.kelly_calculator import KellyCalculator
    17	from modules.live_monitor import LiveMonitor
    18	from modules.pdf_generator import PDFGenerator
    19	from modules.telegram_notifier import TelegramNotifier
    20	from modules.supabase_client import SupabaseClient
    21	
    22	# Configure logging
    23	logging.basicConfig(
    24	    level=logging.INFO,
    25	    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    26	)
    27	logger = logging.getLogger(__name__)
    28	
    29	# Teams to analyze
    30	TEAMS = {
    31	    'FC Porto': 212,
    32	    'Benfica': 211,
    33	    'Sporting': 228
    34	}
    35	
    36	class TeamSpecialistBot:
    37	    def __init__(self):
    38	        self.data_collector = DataCollector()
    39	        self.minimum_analyzer = MinimumAnalyzer()
    40	        self.trigger_detector = TriggerDetector()
    41	        self.kelly_calculator = KellyCalculator()
    42	        self.live_monitor = LiveMonitor()
    43	        self.pdf_generator = PDFGenerator()
    44	        self.telegram = TelegramNotifier()
    45	        self.supabase = SupabaseClient()
    46	        
    47	    def run_full_analysis(self):
    48	        """Complete 5-year analysis for all 3 teams"""
    49	        logger.info("Starting full team analysis...")
    50	        
    51	        for team_name, team_id in TEAMS.items():
    52	            try:
    53	                logger.info(f"Analyzing {team_name}...")
    54	                
    55	                # 1. Collect 5 years of data
    56	                historical_data = self.data_collector.get_team_history(
    57	                    team_id=team_id,
    58	                    years=5
    59	                )
    60	                
    61	                # 2. Calculate minimum values (70%, 80%, 90%)
    62	                minimum_stats = self.minimum_analyzer.calculate_minimums(
    63	                    historical_data
    64	                )
    65	                
    66	                # 3. Detect historical triggers
    67	                triggers = self.trigger_detector.analyze_patterns(
    68	                    historical_data,
    69	                    minimum_stats
    70	                )
    71	                
    72	                # 4. Save to database
    73	                analysis_data = {
    74	                    'team_name': team_name,
    75	                    'team_id': team_id,
    76	                    'analysis_date': datetime.now().isoformat(),
    77	                    'home_stats': minimum_stats['home'],
    78	                    'away_stats': minimum_stats['away'],
    79	                    'special_triggers': triggers['pre_match'],
    80	                    'half_time_patterns': triggers['live_ht'],
    81	                    'min_70_confidence': minimum_stats['min_70'],
    82	                    'min_80_confidence': minimum_stats['min_80'],
    83	                    'min_90_confidence': minimum_stats['min_90'],
    84	                    'total_matches_analyzed': len(historical_data),
    85	                    'date_range_start': (datetime.now() - timedelta(days=365*5)).isoformat(),
    86	                    'date_range_end': datetime.now().isoformat()
    87	                }
    88	                
    89	                self.supabase.save_team_analysis(analysis_data)
    90	                logger.info(f"✅ {team_name} analysis saved")
    91	                
    92	            except Exception as e:
    93	                logger.error(f"Error analyzing {team_name}: {e}")
    94	                
    95	        # Generate consolidated PDF
    96	        logger.info("Generating PDF report...")
    97	        pdf_path = self.pdf_generator.create_full_report(TEAMS.keys())
    98	        
    99	        # Send to Telegram
   100	        self.telegram.send_report(pdf_path)
   101	        logger.info("Full analysis complete!")
   102	        
   103	    def check_upcoming_matches(self):
   104	        """Check upcoming matches and create trading plans"""
   105	        logger.info("Checking upcoming matches...")
   106	        
   107	        for team_name, team_id in TEAMS.items():
   108	            try:
   109	                # Get next 7 days fixtures
   110	                upcoming = self.data_collector.get_upcoming_fixtures(
   111	                    team_id=team_id,
   112	                    days=7
   113	                )
   114	                
   115	                for match in upcoming:
   116	                    # Get latest team analysis
   117	                    analysis = self.supabase.get_team_analysis(team_name)
   118	                    
   119	                    if not analysis:
   120	                        logger.warning(f"No analysis found for {team_name}")
   121	                        continue
   122	                    
   123	                    # Detect active triggers for this match
   124	                    active_triggers = self.trigger_detector.check_match_triggers(
   125	                        match, analysis
   126	                    )
   127	                    
   128	                    if not active_triggers:
   129	                        continue
   130	                    
   131	                    # Calculate Kelly stakes
   132	                    trading_plan = self.kelly_calculator.create_trading_plan(
   133	                        match=match,
   134	                        analysis=analysis,
   135	                        triggers=active_triggers
   136	                    )
   137	                    
   138	                    # Save trading plan
   139	                    plan_data = {
   140	                        'team_name': team_name,
   141	                        'match_date': match['date'],
   142	                        'opponent': match['opponent'],
   143	                        'competition': match['competition'],
   144	                        'is_home': match['is_home'],
   145	                        'active_triggers': active_triggers,
   146	                        'trading_plan': trading_plan,
   147	                        'kelly_stake_recommendation': trading_plan['recommended_stake'],
   148	                        'min_70_scenarios': trading_plan['scenarios']['min_70'],
   149	                        'min_80_scenarios': trading_plan['scenarios']['min_80'],
   150	                        'min_90_scenarios': trading_plan['scenarios']['min_90'],
   151	                        'created_at': datetime.now().isoformat()
   152	                    }
   153	                    
   154	                    self.supabase.save_trading_plan(plan_data)
   155	                    
   156	                    # Send alert
   157	                    self.telegram.send_match_alert(team_name, match, trading_plan)
   158	                    logger.info(f"✅ Trading plan created: {team_name} vs {match['opponent']}")
   159	                    
   160	            except Exception as e:
   161	                logger.error(f"Error checking {team_name} fixtures: {e}")
   162	                
   163	    def monitor_live_matches(self):
   164	        """Monitor live matches for HT triggers (30-45min)"""
   165	        logger.info("Monitoring live matches...")
   166	        
   167	        for team_name, team_id in TEAMS.items():
   168	            try:
   169	                # Get live matches
   170	                live_matches = self.data_collector.get_live_matches(team_id)
   171	                
   172	                for match in live_matches:
   173	                    # Check if between 30-45 minutes
   174	                    if match['elapsed_time'] < 30:
   175	                        continue
   176	                    
   177	                    # Get team analysis
   178	                    analysis = self.supabase.get_team_analysis(team_name)
   179	                    
   180	                    # Detect live HT triggers
   181	                    ht_triggers = self.live_monitor.check_halftime_triggers(
   182	                        match, analysis
   183	                    )
   184	                    
   185	                    if ht_triggers:
   186	                        # Calculate live Kelly recommendations
   187	                        live_plan = self.kelly_calculator.create_live_plan(
   188	                            match, analysis, ht_triggers
   189	                        )
   190	                        
   191	                        # Update trading plan with live data
   192	                        self.supabase.update_trading_plan_live(
   193	                            match['id'],
   194	                            {
   195	                                'live_triggers': ht_triggers,
   196	                                'live_recommendations': live_plan,
   197	                                'ht_score': match['ht_score'],
   198	                                'ht_detected_at': datetime.now().isoformat()
   199	                            }
   200	                        )
   201	                        
   202	                        # Send live alert
   203	                        self.telegram.send_live_alert(team_name, match, live_plan)
   204	                        logger.info(f"🔴 LIVE: {team_name} - HT triggers detected!")
   205	                        
   206	            except Exception as e:
   207	                logger.error(f"Error monitoring {team_name}: {e}")
   208	
   209	def main():
   210	    bot = TeamSpecialistBot()
   211	    scheduler = Scheduler()
   212	    
   213	    # Full analysis: Every Sunday at 02:00 (weekly update)
   214	    scheduler.add_cron_job(
   215	        bot.run_full_analysis,
   216	        day_of_week='sun',
   217	        hour=2,
   218	        minute=0
   219	    )
   220	    
   221	    # Check upcoming matches: Every day at 10:00 and 18:00
   222	    scheduler.add_cron_job(
   223	        bot.check_upcoming_matches,
   224	        hour='10,18',
   225	        minute=0
   226	    )
   227	    
   228	    # Monitor live matches: Every 5 minutes during match hours
   229	    scheduler.add_interval_job(
   230	        bot.monitor_live_matches,
   231	        minutes=5
   232	    )
   233	    
   234	    # Run initial analysis on startup
   235	    logger.info("Running initial analysis...")
   236	    bot.run_full_analysis()
   237	    bot.check_upcoming_matches()
   238	    
   239	    # Start scheduler
   240	    logger.info("Bot started! Monitoring 3 teams...")
   241	    scheduler.start()
   242	
   243	if __name__ == "__main__":
   244	    main()
