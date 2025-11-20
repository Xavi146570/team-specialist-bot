"""
Cleanup Automático de Apostas Órfãs
Previne acumulação de apostas pending de jogos antigos
"""

import os
from datetime import datetime, timedelta
from supabase import create_client
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cleanup_orphan_pending_bets():
    """
    Marca como 'expired' apostas pending com >48h
    Executa diariamente às 03:00 UTC
    """
    try:
        logger.info("🧹 CLEANUP: Iniciando verificação de apostas órfãs...")
        
        # Buscar apostas pending com >48h
        cutoff_date = (datetime.utcnow() - timedelta(hours=48)).isoformat()
        
        response = supabase.table('bet_history')\
            .select('id, created_at')\
            .eq('result', 'pending')\
            .lt('created_at', cutoff_date)\
            .execute()
        
        orphan_bets = response.data
        
        if not orphan_bets:
            logger.info("✅ CLEANUP: Nenhuma aposta órfã encontrada")
            return 0
        
        logger.info(f"📊 CLEANUP: {len(orphan_bets)} apostas órfãs detectadas")
        
        # Marcar como expired
        for bet in orphan_bets:
            supabase.table('bet_history')\
                .update({'result': 'expired'})\
                .eq('id', bet['id'])\
                .execute()
        
        logger.info(f"✅ CLEANUP: {len(orphan_bets)} apostas marcadas como 'expired'")
        
        return len(orphan_bets)
        
    except Exception as e:
        logger.error(f"❌ CLEANUP: Erro ao limpar apostas órfãs: {str(e)}")
        return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cleanup_orphan_pending_bets()
