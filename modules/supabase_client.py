1	"""
     2	Supabase Client - Database integration
     3	Writes to team_specialist_analysis and team_trading_plans tables
     4	"""
     5	
     6	import logging
     7	import os
     8	from supabase import create_client, Client
     9	from typing import Dict, List, Optional
    10	from datetime import datetime
    11	
    12	logger = logging.getLogger(__name__)
    13	
    14	class SupabaseClient:
    15	    def __init__(self):
    16	        self.url = os.getenv('SUPABASE_URL')
    17	        self.key = os.getenv('SUPABASE_SERVICE_KEY')
    18	        self.client: Client = create_client(self.url, self.key)
    19	        
    20	    def save_team_analysis(self, analysis_data: Dict) -> bool:
    21	        """
    22	        Save team analysis to team_specialist_analysis table
    23	        Upserts based on team_name
    24	        """
    25	        try:
    26	            result = self.client.table('team_specialist_analysis').upsert(
    27	                analysis_data,
    28	                on_conflict='team_name'
    29	            ).execute()
    30	            
    31	            logger.info(f"✅ Analysis saved for {analysis_data['team_name']}")
    32	            return True
    33	            
    34	        except Exception as e:
    35	            logger.error(f"Error saving analysis: {e}")
    36	            return False
    37	            
    38	    def get_team_analysis(self, team_name: str) -> Optional[Dict]:
    39	        """Get latest analysis for team"""
    40	        try:
    41	            result = self.client.table('team_specialist_analysis').select('*').eq(
    42	                'team_name', team_name
    43	            ).order('analysis_date', desc=True).limit(1).execute()
    44	            
    45	            if result.data:
    46	                return result.data[0]
    47	            return None
    48	            
    49	        except Exception as e:
    50	            logger.error(f"Error fetching analysis: {e}")
    51	            return None
    52	            
    53	    def save_trading_plan(self, plan_data: Dict) -> bool:
    54	        """
    55	        Save trading plan to team_trading_plans table
    56	        """
    57	        try:
    58	            result = self.client.table('team_trading_plans').insert(
    59	                plan_data
    60	            ).execute()
    61	            
    62	            logger.info(f"✅ Trading plan saved: {plan_data['team_name']} vs {plan_data['opponent']}")
    63	            return True
    64	            
    65	        except Exception as e:
    66	            logger.error(f"Error saving trading plan: {e}")
    67	            return False
    68	            
    69	    def update_trading_plan_live(self, match_id: str, live_data: Dict) -> bool:
    70	        """Update trading plan with live HT data"""
    71	        try:
    72	            result = self.client.table('team_trading_plans').update(
    73	                live_data
    74	            ).eq('match_id', match_id).execute()
    75	            
    76	            logger.info(f"✅ Live data updated for match {match_id}")
    77	            return True
    78	            
    79	        except Exception as e:
    80	            logger.error(f"Error updating live data: {e}")
    81	            return False
    82	            
    83	    def get_upcoming_plans(self, days: int = 7) -> List[Dict]:
    84	        """Get upcoming trading plans"""
    85	        try:
    86	            from datetime import timedelta
    87	            future_date = (datetime.now() + timedelta(days=days)).isoformat()
    88	            
    89	            result = self.client.table('team_trading_plans').select('*').gte(
    90	                'match_date', datetime.now().isoformat()
    91	            ).lte(
    92	                'match_date', future_date
    93	            ).order('match_date', desc=False).execute()
    94	            
    95	            return result.data or []
    96	            
    97	        except Exception as e:
    98	            logger.error(f"Error fetching upcoming plans: {e}")
    99	            return []
