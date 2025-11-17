1	"""
     2	Live Monitor - Track matches between 30-45 minutes for HT triggers
     3	"""
     4	
     5	import logging
     6	from typing import Dict, List
     7	
     8	logger = logging.getLogger(__name__)
     9	
    10	class LiveMonitor:
    11	    def check_halftime_triggers(self, match: Dict, analysis: Dict) -> List[str]:
    12	        """
    13	        Check for active HT triggers during live match
    14	        Focuses on 30-45 minute window
    15	        """
    16	        elapsed = match.get('elapsed_time', 0)
    17	        
    18	        # Only process during HT window (30-45 min)
    19	        if elapsed < 30 or elapsed > 45:
    20	            return []
    21	            
    22	        triggers = []
    23	        ht_patterns = analysis.get('half_time_patterns', {})
    24	        ht_score = match.get('ht_score', {})
    25	        is_home = match['is_home']
    26	        
    27	        team_score = ht_score.get('home', 0) if is_home else ht_score.get('away', 0)
    28	        opponent_score = ht_score.get('away', 0) if is_home else ht_score.get('home', 0)
    29	        
    30	        # Check 0-0 trigger
    31	        if team_score == 0 and opponent_score == 0:
    32	            trigger_key = 'ht_0x0_after_30min_home' if is_home else 'ht_0x0_after_30min_away'
    33	            if trigger_key in ht_patterns:
    34	                pattern = ht_patterns[trigger_key]
    35	                if pattern.get('total_occurrences', 0) > 5:  # Minimum sample size
    36	                    triggers.append({
    37	                        'type': trigger_key,
    38	                        'confidence': pattern.get('confidence', 'medium'),
    39	                        'historical_2h_goals': pattern.get('second_half_goals', 0),
    40	                        'win_probability': pattern.get('win_from_00', 0),
    41	                        'recommended_bet': 'Over 1.5 Goals 2nd Half'
    42	                    })
    43	                    
    44	        # Check winning 1-0 trigger (home only)
    45	        if is_home and team_score == 1 and opponent_score == 0:
    46	            trigger_key = 'ht_1x0_winning_home'
    47	            if trigger_key in ht_patterns:
    48	                pattern = ht_patterns[trigger_key]
    49	                triggers.append({
    50	                    'type': trigger_key,
    51	                    'confidence': pattern.get('confidence', 'high'),
    52	                    'maintain_win_rate': pattern.get('maintained_win', 0),
    53	                    'clean_sheet_probability': pattern.get('clean_sheet_rate', 0),
    54	                    'recommended_bet': 'Home Win + Clean Sheet'
    55	                })
    56	                
    57	        # Check losing at HT (home only)
    58	        if is_home and team_score < opponent_score:
    59	            trigger_key = 'ht_losing_home'
    60	            if trigger_key in ht_patterns:
    61	                pattern = ht_patterns[trigger_key]
    62	                if pattern.get('comeback_rate', 0) > 30:  # At least 30% comeback rate
    63	                    triggers.append({
    64	                        'type': trigger_key,
    65	                        'confidence': pattern.get('confidence', 'medium'),
    66	                        'comeback_rate': pattern.get('comeback_rate', 0),
    67	                        'second_half_goals': pattern.get('second_half_goals', 0),
    68	                        'recommended_bet': 'Team to Score Next / Comeback'
    69	                    })
    70	                    
    71	        # Check drawing at HT (away only)
    72	        if not is_home and team_score == opponent_score:
    73	            trigger_key = 'ht_drawing_away'
    74	            if trigger_key in ht_patterns:
    75	                pattern = ht_patterns[trigger_key]
    76	                triggers.append({
    77	                    'type': trigger_key,
    78	                    'confidence': pattern.get('confidence', 'medium'),
    79	                    'win_from_draw': pattern.get('win_from_draw', 0),
    80	                    'second_half_btts': pattern.get('second_half_btts', 0),
    81	                    'recommended_bet': 'BTTS 2nd Half'
    82	                })
    83	                
    84	        # Log detected triggers
    85	        if triggers:
    86	            logger.info(f"🔴 LIVE HT TRIGGERS: {match['opponent']} - {len(triggers)} triggers active at {elapsed}min")
    87	            
    88	        return triggers
    89	        
    90	    def should_send_alert(self, triggers: List[str], last_alert_time: Dict) -> bool:
    91	        """
    92	        Prevent duplicate alerts
    93	        Only send once per HT period
    94	        """
    95	        if not triggers:
    96	            return False
    97	            
    98	        match_id = triggers[0].get('match_id', '')
    99	        
   100	        # Check if already alerted for this HT
   101	        if match_id in last_alert_time:
   102	            return False
   103	            
   104	        return True
