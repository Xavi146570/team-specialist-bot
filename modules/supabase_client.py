"""
Supabase Client - Database integration
Writes to team_specialist_analysis and team_trading_plans tables
"""

import logging
import os
from supabase import create_client, Client
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_SERVICE_KEY')
        self.client: Client = create_client(self.url, self.key)
        
    def save_team_analysis(self, analysis_data: Dict) -> bool:
        """
        Save team analysis to team_specialist_analysis table
        Upserts based on team_name
        """
        try:
            result = self.client.table('team_specialist_analysis').upsert(
                analysis_data,
                on_conflict='team_name'
            ).execute()
            
            logger.info(f"✅ Analysis saved for {analysis_data['team_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return False
            
    def get_team_analysis(self, team_name: str) -> Optional[Dict]:
        """Get latest analysis for team"""
        try:
            result = self.client.table('team_specialist_analysis').select('*').eq(
                'team_name', team_name
            ).order('analysis_date', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching analysis: {e}")
            return None
            
    def save_trading_plan(self, plan_data: Dict) -> bool:
        """
        Save trading plan to team_trading_plans table
        """
        try:
            result = self.client.table('team_trading_plans').insert(
                plan_data
            ).execute()
            
            logger.info(f"✅ Trading plan saved: {plan_data['team_name']} vs {plan_data['opponent']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trading plan: {e}")
            return False
            
    def update_trading_plan_live(self, match_id: str, live_data: Dict) -> bool:
        """Update trading plan with live HT data"""
        try:
            result = self.client.table('team_trading_plans').update(
                live_data
            ).eq('match_id', match_id).execute()
            
            logger.info(f"✅ Live data updated for match {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating live data: {e}")
            return False
            
    def get_upcoming_plans(self, days: int = 7) -> List[Dict]:
        """Get upcoming trading plans"""
        try:
            from datetime import timedelta
            future_date = (datetime.now() + timedelta(days=days)).isoformat()
            
            result = self.client.table('team_trading_plans').select('*').gte(
                'match_date', datetime.now().isoformat()
            ).lte(
                'match_date', future_date
            ).order('match_date', desc=False).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error fetching upcoming plans: {e}")
            return []
