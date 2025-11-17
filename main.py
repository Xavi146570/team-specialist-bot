"""
Team Specialist Bot - FC Porto, Benfica, Sporting Analysis
Analyzes 3 biggest Portuguese teams with MINIMUM values (not averages)
Uses Kelly Criterion for stake sizing
Monitors live HT triggers after 30 minutes
"""

import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

from modules.data_collector import DataCollector
from modules.minimum_analyzer import MinimumAnalyzer
from modules.trigger_detector import TriggerDetector
from modules.kelly_calculator import KellyCalculator
from modules.live_monitor import LiveMonitor
from modules.pdf_generator import PDFGenerator
from modules.telegram_notifier import TelegramNotifier
from modules.supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Teams to analyze
TEAMS = {
    'FC Porto': 212,
    'Benfica': 211,
    'Sporting': 228
}

class TeamSpecialistBot:
    def __init__(self):
        self.data_collector = DataCollector()
        self.minimum_analyzer = MinimumAnalyzer()
        self.trigger_detector = TriggerDetector()
        self.kelly_calculator = KellyCalculator()
        self.live_monitor = LiveMonitor()
        self.pdf_generator = PDFGenerator()
        self.telegram = TelegramNotifier()
        self.supabase = SupabaseClient()
        
    def run_full_analysis(self):
        """Complete 5-year analysis for all 3 teams"""
        logger.info("Starting full team analysis...")
        
        for team_name, team_id in TEAMS.items():
            try:
                logger.info(f"Analyzing {team_name}...")
                
                # 1. Collect 5 years of data
                historical_data = self.data_collector.get_team_history(
                    team_id=team_id,
                    years=5
                )
                
                # 2. Calculate minimum values (70%, 80%, 90%)
                minimum_stats = self.minimum_analyzer.calculate_minimums(
                    historical_data
                )
                
                # 3. Detect historical triggers
                triggers = self.trigger_detector.analyze_patterns(
                    historical_data,
                    minimum_stats
                )
                
                # 4. Save to database
                analysis_data = {
                    'team_name': team_name,
                    'team_id': team_id,
                    'analysis_date': datetime.now().isoformat(),
                    'home_stats': minimum_stats['home'],
                    'away_stats': minimum_stats['away'],
                    'special_triggers': triggers['pre_match'],
                    'half_time_patterns': triggers['live_ht'],
                    'min_70_confidence': minimum_stats['min_70'],
                    'min_80_confidence': minimum_stats['min_80'],
                    'min_90_confidence': minimum_stats['min_90'],
                    'total_matches_analyzed': len(historical_data),
                    'date_range_start': (datetime.now() - timedelta(days=365*5)).isoformat(),
                    'date_range_end': datetime.now().isoformat()
                }
                
                self.supabase.save_team_analysis(analysis_data)
                logger.info(f"✅ {team_name} analysis saved")
                
            except Exception as e:
                logger.error(f"Error analyzing {team_name}: {e}")
                
        # Generate consolidated PDF
        logger.info("Generating PDF report...")
        pdf_path = self.pdf_generator.create_full_report(TEAMS.keys())
        
        # Send to Telegram
        self.telegram.send_report(pdf_path)
        logger.info("Full analysis complete!")
        
    def check_upcoming_matches(self):
        """Check upcoming matches and create trading plans"""
        logger.info("Checking upcoming matches...")
        
        for team_name, team_id in TEAMS.items():
            try:
                # Get next 7 days fixtures
                upcoming = self.data_collector.get_upcoming_fixtures(
                    team_id=team_id,
                    days=7
                )
                
                for match in upcoming:
                    # Get latest team analysis
                    analysis = self.supabase.get_team_analysis(team_name)
                    
                    if not analysis:
                        logger.warning(f"No analysis found for {team_name}")
                        continue
                    
                    # Detect active triggers for this match
                    active_triggers = self.trigger_detector.check_match_triggers(
                        match, analysis
                    )
                    
                    if not active_triggers:
                        continue
                    
                    # Calculate Kelly stakes
                    trading_plan = self.kelly_calculator.create_trading_plan(
                        match=match,
                        analysis=analysis,
                        triggers=active_triggers
                    )
                    
                    # Save trading plan
                    plan_data = {
                        'team_name': team_name,
                        'match_date': match['date'],
                        'opponent': match['opponent'],
                        'competition': match['competition'],
                        'is_home': match['is_home'],
                        'active_triggers': active_triggers,
                        'trading_plan': trading_plan,
                        'kelly_stake_recommendation': trading_plan['recommended_stake'],
                        'min_70_scenarios': trading_plan['scenarios']['min_70'],
                        'min_80_scenarios': trading_plan['scenarios']['min_80'],
                        'min_90_scenarios': trading_plan['scenarios']['min_90'],
                        'created_at': datetime.now().isoformat()
                    }
                    
                    self.supabase.save_trading_plan(plan_data)
                    
                    # Send alert
                    self.telegram.send_match_alert(team_name, match, trading_plan)
                    logger.info(f"✅ Trading plan created: {team_name} vs {match['opponent']}")
                    
            except Exception as e:
                logger.error(f"Error checking {team_name} fixtures: {e}")
                
    def monitor_live_matches(self):
        """Monitor live matches for HT triggers (30-45min)"""
        logger.info("Monitoring live matches...")
        
        for team_name, team_id in TEAMS.items():
            try:
                # Get live matches
                live_matches = self.data_collector.get_live_matches(team_id)
                
                for match in live_matches:
                    # Check if between 30-45 minutes
                    if match['elapsed_time'] < 30:
                        continue
                    
                    # Get team analysis
                    analysis = self.supabase.get_team_analysis(team_name)
                    
                    # Detect live HT triggers
                    ht_triggers = self.live_monitor.check_halftime_triggers(
                        match, analysis
                    )
                    
                    if ht_triggers:
                        # Calculate live Kelly recommendations
                        live_plan = self.kelly_calculator.create_live_plan(
                            match, analysis, ht_triggers
                        )
                        
                        # Update trading plan with live data
                        self.supabase.update_trading_plan_live(
                            match['id'],
                            {
                                'live_triggers': ht_triggers,
                                'live_recommendations': live_plan,
                                'ht_score': match['ht_score'],
                                'ht_detected_at': datetime.now().isoformat()
                            }
                        )
                        
                        # Send live alert
                        self.telegram.send_live_alert(team_name, match, live_plan)
                        logger.info(f"🔴 LIVE: {team_name} - HT triggers detected!")
                        
            except Exception as e:
                logger.error(f"Error monitoring {team_name}: {e}")

def main():
    bot = TeamSpecialistBot()
    scheduler = BlockingScheduler()
    
    # Full analysis: Every Sunday at 02:00 (weekly update)
    scheduler.add_job(
        bot.run_full_analysis,
        'cron',
        day_of_week='sun',
        hour=2,
        minute=0
    )
    
    # Check upcoming matches: Every day at 10:00 and 18:00
    scheduler.add_job(
        bot.check_upcoming_matches,
        'cron',
        hour='10,18',
        minute=0
    )
    
    # Monitor live matches: Every 5 minutes
    scheduler.add_job(
        bot.monitor_live_matches,
        'interval',
        minutes=5
    )
    
    # Run initial analysis on startup
    logger.info("Running initial analysis...")
    try:
        bot.run_full_analysis()
        bot.check_upcoming_matches()
    except Exception as e:
        logger.error(f"Error in initial run: {e}")
    
    # Start scheduler
    logger.info("Bot started! Monitoring 3 teams...")
    scheduler.start()

if __name__ == "__main__":
    main()
