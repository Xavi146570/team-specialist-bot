1	"""
     2	Data Collector - API-Football Integration
     3	Fetches 5 years of historical data + upcoming fixtures + live matches
     4	"""
     5	
     6	import os
     7	import requests
     8	import logging
     9	from datetime import datetime, timedelta
    10	from typing import List, Dict
    11	
    12	logger = logging.getLogger(__name__)
    13	
    14	class DataCollector:
    15	    def __init__(self):
    16	        self.api_key = os.getenv('APIFOOTBALL_API_KEY')
    17	        self.base_url = 'https://v3.football.api-sports.io'
    18	        self.headers = {
    19	            'x-apisports-key': self.api_key
    20	        }
    21	        
    22	    def get_team_history(self, team_id: int, years: int = 5) -> List[Dict]:
    23	        """
    24	        Fetch complete match history for team
    25	        Returns last 5 years of matches
    26	        """
    27	        all_matches = []
    28	        current_year = datetime.now().year
    29	        
    30	        for year in range(current_year - years, current_year + 1):
    31	            try:
    32	                response = requests.get(
    33	                    f'{self.base_url}/fixtures',
    34	                    headers=self.headers,
    35	                    params={
    36	                        'team': team_id,
    37	                        'season': year,
    38	                        'status': 'FT'  # Only finished matches
    39	                    }
    40	                )
    41	                
    42	                if response.status_code == 200:
    43	                    data = response.json()
    44	                    matches = data.get('response', [])
    45	                    
    46	                    for match in matches:
    47	                        all_matches.append(self._parse_match(match, team_id))
    48	                        
    49	                    logger.info(f"Fetched {len(matches)} matches from {year}")
    50	                    
    51	            except Exception as e:
    52	                logger.error(f"Error fetching {year} data: {e}")
    53	                
    54	        logger.info(f"Total matches collected: {len(all_matches)}")
    55	        return all_matches
    56	        
    57	    def get_upcoming_fixtures(self, team_id: int, days: int = 7) -> List[Dict]:
    58	        """Get upcoming fixtures in next N days"""
    59	        try:
    60	            today = datetime.now()
    61	            end_date = today + timedelta(days=days)
    62	            
    63	            response = requests.get(
    64	                f'{self.base_url}/fixtures',
    65	                headers=self.headers,
    66	                params={
    67	                    'team': team_id,
    68	                    'from': today.strftime('%Y-%m-%d'),
    69	                    'to': end_date.strftime('%Y-%m-%d'),
    70	                    'status': 'NS'  # Not started
    71	                }
    72	            )
    73	            
    74	            if response.status_code == 200:
    75	                data = response.json()
    76	                fixtures = data.get('response', [])
    77	                return [self._parse_fixture(f, team_id) for f in fixtures]
    78	                
    79	        except Exception as e:
    80	            logger.error(f"Error fetching upcoming fixtures: {e}")
    81	            
    82	        return []
    83	        
    84	    def get_live_matches(self, team_id: int) -> List[Dict]:
    85	        """Get currently live matches for team"""
    86	        try:
    87	            response = requests.get(
    88	                f'{self.base_url}/fixtures',
    89	                headers=self.headers,
    90	                params={
    91	                    'team': team_id,
    92	                    'live': 'all'
    93	                }
    94	            )
    95	            
    96	            if response.status_code == 200:
    97	                data = response.json()
    98	                live = data.get('response', [])
    99	                return [self._parse_live_match(m, team_id) for m in live]
   100	                
   101	        except Exception as e:
   102	            logger.error(f"Error fetching live matches: {e}")
   103	            
   104	        return []
   105	        
   106	    def _parse_match(self, match_data: Dict, team_id: int) -> Dict:
   107	        """Parse historical match data"""
   108	        fixture = match_data['fixture']
   109	        teams = match_data['teams']
   110	        goals = match_data['goals']
   111	        score = match_data['score']
   112	        
   113	        is_home = teams['home']['id'] == team_id
   114	        opponent = teams['away']['name'] if is_home else teams['home']['name']
   115	        
   116	        team_goals = goals['home'] if is_home else goals['away']
   117	        opponent_goals = goals['away'] if is_home else goals['home']
   118	        
   119	        ht_team = score['halftime']['home'] if is_home else score['halftime']['away']
   120	        ht_opponent = score['halftime']['away'] if is_home else score['halftime']['home']
   121	        
   122	        return {
   123	            'match_id': fixture['id'],
   124	            'date': fixture['date'],
   125	            'competition': match_data['league']['name'],
   126	            'is_home': is_home,
   127	            'opponent': opponent,
   128	            'team_goals': team_goals,
   129	            'opponent_goals': opponent_goals,
   130	            'total_goals': team_goals + opponent_goals,
   131	            'ht_team_goals': ht_team,
   132	            'ht_opponent_goals': ht_opponent,
   133	            'ht_total': ht_team + ht_opponent,
   134	            'result': 'W' if team_goals > opponent_goals else ('D' if team_goals == opponent_goals else 'L'),
   135	            'clean_sheet': opponent_goals == 0,
   136	            'btts': team_goals > 0 and opponent_goals > 0,
   137	            'over_2_5': (team_goals + opponent_goals) > 2.5,
   138	            'over_1_5_ht': (ht_team + ht_opponent) > 1.5
   139	        }
   140	        
   141	    def _parse_fixture(self, fixture_data: Dict, team_id: int) -> Dict:
   142	        """Parse upcoming fixture"""
   143	        fixture = fixture_data['fixture']
   144	        teams = fixture_data['teams']
   145	        
   146	        is_home = teams['home']['id'] == team_id
   147	        opponent = teams['away']['name'] if is_home else teams['home']['name']
   148	        
   149	        return {
   150	            'match_id': fixture['id'],
   151	            'date': fixture['date'],
   152	            'competition': fixture_data['league']['name'],
   153	            'is_home': is_home,
   154	            'opponent': opponent,
   155	            'opponent_id': teams['away']['id'] if is_home else teams['home']['id'],
   156	            'venue': fixture['venue']['name']
   157	        }
   158	        
   159	    def _parse_live_match(self, match_data: Dict, team_id: int) -> Dict:
   160	        """Parse live match data"""
   161	        fixture = match_data['fixture']
   162	        teams = match_data['teams']
   163	        goals = match_data['goals']
   164	        
   165	        is_home = teams['home']['id'] == team_id
   166	        
   167	        return {
   168	            'match_id': fixture['id'],
   169	            'elapsed_time': fixture['status']['elapsed'],
   170	            'is_home': is_home,
   171	            'opponent': teams['away']['name'] if is_home else teams['home']['name'],
   172	            'current_score': f"{goals['home']}-{goals['away']}",
   173	            'ht_score': match_data['score']['halftime'],
   174	            'team_score': goals['home'] if is_home else goals['away'],
   175	            'opponent_score': goals['away'] if is_home else goals['home']
   176	        }
