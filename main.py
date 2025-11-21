"""
Team Specialist Bot - Main Application
Analyzes Benfica, FC Porto, and Sporting matches using historical patterns
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Import custom modules
from modules.data_collector import DataCollector
from modules.trigger_detector import TriggerDetector
from modules.minimum_analyzer import MinimumAnalyzer
from modules.kelly_calculator import KellyCalculator
from modules.live_monitor import LiveMonitor
from modules.supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeamSpecialistBot:
    """Main bot coordinator"""
    
    def __init__(self):
        # Initialize components
        self.db = SupabaseClient()
        self.data_collector = DataCollector()
        self.trigger_detector = TriggerDetector(self.data_collector)
        self.minimum_analyzer = MinimumAnalyzer()
        self.kelly_calculator = KellyCalculator()
        
        # Team IDs
        self.TEAMS = {
            'Benfica': 211,
            'FC Porto': 212,
            'Sporting': 228
        }
    
    def run_weekly_analysis(self):
        """Run weekly historical analysis for all teams"""
        logger.info("🔄 Starting weekly analysis...")
        
        for team_name, team_id in self.TEAMS.items():
            try:
                logger.info(f"Analyzing {team_name}...")
                
                # Get 5 years of historical data
                matches = self.data_collector.get_team_matches(
                    team_id=team_id,
                    season=2024,
                    last=200
                )
                
                if not matches:
                    logger.warning(f"No data found for {team_name}")
                    continue
                
                # Analyze patterns
                analysis = self.trigger_detector.analyze_patterns(team_id, matches)
                
                # Calculate minimum analysis
                minimum_stats = self.minimum_analyzer.analyze(matches, team_id)
                
                # Combine results
                full_analysis = {
                    **analysis,
                    'minimum_stats': minimum_stats,
                    'team_name': team_name,
                    'analysis_date': datetime.utcnow().isoformat()
                }
                
                # Save to database
                self.db.save_analysis(full_analysis)
                
                logger.info(f"✅ Analysis complete for {team_name}")
                
            except Exception as e:
                logger.error(f"Error analyzing {team_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        logger.info("✅ Weekly analysis complete!")
    
    def check_upcoming_matches(self):
        """Check for upcoming matches and create opportunities"""
        logger.info("Checking upcoming matches...")
        
        # Date range for upcoming matches
        today = datetime.now().date()
        end_date = today + timedelta(days=7)
        
        for team_name, team_id in self.TEAMS.items():
            try:
                # Get upcoming matches (next 7 days)
                matches = self.data_collector.get_team_matches(
                    team_id=team_id,
                    season=2024,
                    from_date=today.strftime('%Y-%m-%d'),
                    to_date=end_date.strftime('%Y-%m-%d'),
                    status='NS'
                )
                
                if not matches:
                    logger.info(f"⏭️ No upcoming matches for {team_name}")
                    continue
                
                logger.info(f"✅ Found {len(matches)} upcoming matches for {team_name}")
                
                # Analyze each match
                for match in matches:
                    try:
                        home_name = match['teams']['home']['name']
                        away_name = match['teams']['away']['name']
                        match_id = match['fixture']['id']
                        
                        logger.info(f"🎯 Analyzing: {home_name} vs {away_name}")
                        
                        # Get analysis
                        analysis = self.db.get_latest_analysis(team_name)
                        
                        if not analysis:
                            logger.warning(f"⚠️ No analysis found for {team_name}")
                            continue
                        
                        # Check triggers
                        active_triggers = self.trigger_detector.check_match_triggers(
                            match,
                            analysis
                        )
                        
                        logger.info(f"📊 Triggers detected: {len(active_triggers)}")
                        
                        # Create opportunity if enough triggers
                        if len(active_triggers) >= 3:
                            logger.info("✅ Creating trading plan...")
                            
                            # Calculate confidence
                            confidence = self.trigger_detector.calculate_trigger_score(
                                active_triggers,
                                analysis
                            )
                            
                            # Create trading plan
                            plan = {
                                'team_name': team_name,
                                'match_id': match_id,
                                'opponent': away_name if match['teams']['home']['id'] == team_id else home_name,
                                'match_date': match['fixture']['date'],
                                'league': match['league']['name'],
                                'triggers': active_triggers,
                                'confidence': confidence,
                                'analysis': analysis,
                                'recommended_markets': self._get_recommended_markets(analysis, active_triggers)
                            }
                            
                            # Save to database
                            self.db.save_trading_plan(plan)
                            
                            # Create opportunity for frontend
                            self._create_opportunity(plan)
                            
                            logger.info(f"🎯 Opportunity created for {home_name} vs {away_name}")
                        else:
                            logger.info(f"⏭️ Skipping - insufficient triggers ({len(active_triggers)}/3)")
                    
                    except Exception as e:
                        logger.error(f"❌ Error analyzing match: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        continue
            
            except Exception as e:
                logger.error(f"❌ Error checking {team_name} fixtures: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
    
    def _create_opportunity(self, plan: Dict):
        """Create opportunity record for frontend"""
        opportunity = {
            'bot_name': 'Team Specialist Bot',
            'match_info': f"{plan['opponent']} vs {plan['team_name']}" if plan['team_name'] in ['Benfica', 'FC Porto', 'Sporting'] else f"{plan['team_name']} vs {plan['opponent']}",
            'league': plan['league'],
            'market': plan['recommended_markets'][0] if plan['recommended_markets'] else 'Over 2.5',
            'odd': 1.85,
            'confidence': plan['confidence'],
            'status': 'pre-match',
            'match_date': plan['match_date'],
            'analysis': f"{plan['team_name']}: {len(plan['triggers'])} triggers active",
            'match_id': str(plan['match_id'])
        }
        
        self.db.create_opportunity(opportunity)
    
    def _get_recommended_markets(self, analysis: Dict, triggers: List[str]) -> List[str]:
        """Get recommended markets based on analysis"""
        markets = []
        
        if 'vs_bottom5_home' in triggers or 'vs_bottom5_away' in triggers:
            markets.append('Over 2.5')
            markets.append('BTTS')
        
        if 'classico' in triggers:
            markets.append('Over 2.5 + BTTS')
        
        if 'champions_week' in triggers:
            markets.append('Under 2.5')
        
        return markets if markets else ['Over 2.5']
    
    def monitor_live_matches(self):
        """Monitor live matches for in-play opportunities"""
        try:
            live_monitor = LiveMonitor(
                self.data_collector,
                self.trigger_detector,
                self.db
            )
            
            for team_name, team_id in self.TEAMS.items():
                live_monitor.check_live_matches(team_id, team_name)
        
        except Exception as e:
            logger.error(f"Error in live monitoring: {e}")

def main():
    """Main application entry point"""
    logger.info("🚀 Team Specialist Bot started!")
    
    bot = TeamSpecialistBot()
    
    scheduler = BlockingScheduler()
    
    scheduler.add_job(
        bot.run_weekly_analysis,
        CronTrigger(day_of_week='wed', hour=10, minute=0),
        id='weekly_analysis',
        name='Weekly Historical Analysis'
    )
    
    scheduler.add_job(
        bot.check_upcoming_matches,
        CronTrigger(hour=7, minute=0),
        id='daily_check',
        name='Daily Match Check'
    )
    
    scheduler.add_job(
        bot.monitor_live_matches,
        'interval',
        minutes=2,
        id='live_monitor',
        name='Live Match Monitor'
    )
    
    logger.info("📅 Scheduled jobs:")
    logger.info("  - Weekly analysis: Wednesday 10:00")
    logger.info("  - Daily match check: Every day 7:00")
    logger.info("  - Live monitoring: Every 2 minutes")
    
    logger.info("🧪 Running initial check...")
    bot.check_upcoming_matches()
    
    logger.info("⏰ Starting scheduler...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Shutting down...")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
