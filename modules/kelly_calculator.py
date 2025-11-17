1	"""
     2	Kelly Criterion Calculator - Stake sizing based on MINIMUM probabilities
     3	f = (bp - q) / b
     4	"""
     5	
     6	import logging
     7	from typing import Dict, List
     8	
     9	logger = logging.getLogger(__name__)
    10	
    11	class KellyCalculator:
    12	    def __init__(self):
    13	        self.max_kelly_fraction = 0.25  # Never bet more than 25% of bankroll
    14	        
    15	    def create_trading_plan(self, match: Dict, analysis: Dict, triggers: List[str]) -> Dict:
    16	        """
    17	        Create complete trading plan with Kelly stakes
    18	        Based on MINIMUM probabilities (70%, 80%, 90%)
    19	        """
    20	        is_home = match['is_home']
    21	        venue_stats = analysis['home_stats'] if is_home else analysis['away_stats']
    22	        
    23	        scenarios = {
    24	            'min_70': self._calculate_scenarios(venue_stats, analysis['min_70_confidence'], 'conservative'),
    25	            'min_80': self._calculate_scenarios(venue_stats, analysis['min_80_confidence'], 'moderate'),
    26	            'min_90': self._calculate_scenarios(venue_stats, analysis['min_90_confidence'], 'aggressive')
    27	        }
    28	        
    29	        # Select recommended scenario based on triggers
    30	        confidence_level = self._select_confidence_level(triggers)
    31	        recommended = scenarios[confidence_level]
    32	        
    33	        return {
    34	            'match_id': match['match_id'],
    35	            'confidence_level': confidence_level,
    36	            'recommended_stake': recommended['kelly_stake'],
    37	            'scenarios': scenarios,
    38	            'primary_bet': recommended['primary_bet'],
    39	            'backup_bets': recommended['backup_bets'],
    40	            'entry_phases': self._create_entry_phases(recommended),
    41	            'stop_loss': recommended['stop_loss'],
    42	            'take_profit': recommended['take_profit']
    43	        }
    44	        
    45	    def create_live_plan(self, match: Dict, analysis: Dict, ht_triggers: List[str]) -> Dict:
    46	        """Create live trading plan for HT triggers"""
    47	        ht_patterns = analysis.get('half_time_patterns', {})
    48	        
    49	        # Select pattern based on current HT situation
    50	        pattern_key = self._detect_ht_pattern(match, ht_triggers)
    51	        
    52	        if pattern_key not in ht_patterns:
    53	            return {'status': 'no_pattern_matched'}
    54	            
    55	        pattern = ht_patterns[pattern_key]
    56	        
    57	        # Calculate live Kelly stake
    58	        live_odds = 2.0  # Placeholder - would come from live odds feed
    59	        probability = pattern.get('second_half_over_15', 0) / 100
    60	        
    61	        kelly = self.calculate_kelly(probability, live_odds)
    62	        
    63	        return {
    64	            'trigger': pattern_key,
    65	            'kelly_stake': kelly,
    66	            'suggested_bet': 'Over 1.5 Goals 2nd Half',
    67	            'probability': f'{probability * 100:.1f}%',
    68	            'odds_needed': live_odds,
    69	            'max_stake': f'{kelly * 100:.2f}%',
    70	            'timing': 'HT - 2nd half kickoff'
    71	        }
    72	        
    73	    def calculate_kelly(self, probability: float, odds: float) -> float:
    74	        """
    75	        Kelly Criterion formula
    76	        f = (bp - q) / b
    77	        
    78	        f = fraction of bankroll
    79	        b = odds - 1
    80	        p = probability of win
    81	        q = probability of loss (1 - p)
    82	        """
    83	        if probability <= 0 or odds <= 1:
    84	            return 0.0
    85	            
    86	        b = odds - 1
    87	        p = probability
    88	        q = 1 - p
    89	        
    90	        kelly = (b * p - q) / b
    91	        
    92	        # Never bet if Kelly is negative (no edge)
    93	        if kelly <= 0:
    94	            return 0.0
    95	            
    96	        # Cap at max fraction (risk management)
    97	        kelly = min(kelly, self.max_kelly_fraction)
    98	        
    99	        return kelly
   100	        
   101	    def _calculate_scenarios(self, venue_stats: Dict, min_confidence: Dict, strategy: str) -> Dict:
   102	        """Calculate betting scenarios for confidence level"""
   103	        
   104	        # Extract minimum values
   105	        min_team_goals = min_confidence.get('minimum_team_goals', 1.5)
   106	        min_total_goals = min_confidence.get('minimum_total_goals', 2.5)
   107	        
   108	        # Base probabilities (from historical minimums)
   109	        prob_over_15 = 0.7 if strategy == 'conservative' else 0.8 if strategy == 'moderate' else 0.9
   110	        prob_over_25 = 0.6 if strategy == 'conservative' else 0.7 if strategy == 'moderate' else 0.8
   111	        
   112	        # Placeholder odds (would come from bookmaker API)
   113	        odds_over_15 = 1.5
   114	        odds_over_25 = 2.0
   115	        odds_btts = 1.8
   116	        
   117	        kelly_over_15 = self.calculate_kelly(prob_over_15, odds_over_15)
   118	        kelly_over_25 = self.calculate_kelly(prob_over_25, odds_over_25)
   119	        kelly_btts = self.calculate_kelly(0.65, odds_btts)
   120	        
   121	        return {
   122	            'strategy': strategy,
   123	            'primary_bet': {
   124	                'market': 'Over 1.5 Goals',
   125	                'probability': f'{prob_over_15 * 100:.0f}%',
   126	                'odds': odds_over_15,
   127	                'kelly_stake': f'{kelly_over_15 * 100:.2f}%',
   128	                'minimum_guarantee': f'{min_team_goals:.1f} goals'
   129	            },
   130	            'backup_bets': [
   131	                {
   132	                    'market': 'Over 2.5 Goals',
   133	                    'probability': f'{prob_over_25 * 100:.0f}%',
   134	                    'odds': odds_over_25,
   135	                    'kelly_stake': f'{kelly_over_25 * 100:.2f}%'
   136	                },
   137	                {
   138	                    'market': 'BTTS',
   139	                    'probability': '65%',
   140	                    'odds': odds_btts,
   141	                    'kelly_stake': f'{kelly_btts * 100:.2f}%'
   142	                }
   143	            ],
   144	            'kelly_stake': max(kelly_over_15, kelly_over_25),
   145	            'stop_loss': '50% of stake',
   146	            'take_profit': '80% profit target'
   147	        }
   148	        
   149	    def _create_entry_phases(self, scenario: Dict) -> List[Dict]:
   150	        """Create phased entry strategy"""
   151	        total_kelly = float(scenario['kelly_stake'].replace('%', ''))
   152	        
   153	        return [
   154	            {
   155	                'phase': 'Pre-match',
   156	                'stake': f'{total_kelly * 0.4:.2f}%',
   157	                'timing': '30 minutes before kickoff',
   158	                'markets': ['Over 1.5 Goals']
   159	            },
   160	            {
   161	                'phase': 'Live Entry 1',
   162	                'stake': f'{total_kelly * 0.3:.2f}%',
   163	                'timing': '15-20 minutes if 0-0',
   164	                'markets': ['Over 1.5 Goals', 'Team to score']
   165	            },
   166	            {
   167	                'phase': 'Live Entry 2',
   168	                'stake': f'{total_kelly * 0.3:.2f}%',
   169	                'timing': 'HT if triggers active',
   170	                'markets': ['2nd Half Over 0.5', '2nd Half Over 1.5']
   171	            }
   172	        ]
   173	        
   174	    def _select_confidence_level(self, triggers: List[str]) -> str:
   175	        """Select confidence level based on active triggers"""
   176	        high_confidence_triggers = ['vs_bottom5_home', 'classico', 'post_loss_home']
   177	        
   178	        if any(t in triggers for t in high_confidence_triggers):
   179	            return 'min_80'
   180	        elif len(triggers) >= 2:
   181	            return 'min_80'
   182	        else:
   183	            return 'min_70'
   184	            
   185	    def _detect_ht_pattern(self, match: Dict, ht_triggers: List[str]) -> str:
   186	        """Detect which HT pattern is active"""
   187	        ht_score = match.get('ht_score', {})
   188	        
   189	        if ht_score.get('home') == 0 and ht_score.get('away') == 0:
   190	            return 'ht_0x0_after_30min_home' if match['is_home'] else 'ht_0x0_after_30min_away'
   191	        elif match['is_home'] and ht_score.get('home', 0) > ht_score.get('away', 0):
   192	            return 'ht_1x0_winning_home'
   193	        elif match['is_home'] and ht_score.get('home', 0) < ht_score.get('away', 0):
   194	            return 'ht_losing_home'
   195	        else:
   196	            return 'ht_drawing_away'
