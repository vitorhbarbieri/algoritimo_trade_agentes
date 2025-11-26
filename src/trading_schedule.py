"""
Sistema de horário de funcionamento baseado no horário da B3.
"""

from datetime import datetime, time, timedelta
from typing import Tuple, Optional
import pytz

# Timezone da B3 (America/Sao_Paulo)
B3_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# Horários da B3
B3_PRE_OPEN = time(9, 45)  # 09:45 - Pré-abertura
B3_OPEN = time(10, 0)      # 10:00 - Abertura
B3_CLOSE = time(17, 0)     # 17:00 - Fechamento
B3_POST_CLOSE = time(17, 30)  # 17:30 - Pós-fechamento


class TradingSchedule:
    """Gerencia horário de funcionamento baseado na B3."""
    
    def __init__(self, timezone=None):
        self.timezone = timezone or B3_TIMEZONE
    
    def get_current_b3_time(self) -> datetime:
        """Retorna hora atual no timezone da B3."""
        return datetime.now(self.timezone)
    
    def is_trading_day(self, date: Optional[datetime] = None) -> bool:
        """
        Verifica se é dia útil (segunda a sexta).
        Não verifica feriados (pode ser adicionado depois).
        """
        if date is None:
            date = self.get_current_b3_time()
        
        # Segunda = 0, Sexta = 4
        return date.weekday() < 5
    
    def is_trading_hours(self, current_time: Optional[datetime] = None) -> bool:
        """
        Verifica se está dentro do horário de negociação da B3.
        Horário: 10:00 - 17:00 (horário de Brasília)
        """
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        if not self.is_trading_day(current_time):
            return False
        
        current_time_only = current_time.time()
        
        # Entre 10:00 e 17:00
        return B3_OPEN <= current_time_only < B3_CLOSE
    
    def is_pre_market(self, current_time: Optional[datetime] = None) -> bool:
        """Verifica se está no pré-mercado (09:45 - 10:00)."""
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        if not self.is_trading_day(current_time):
            return False
        
        current_time_only = current_time.time()
        return B3_PRE_OPEN <= current_time_only < B3_OPEN
    
    def is_post_market(self, current_time: Optional[datetime] = None) -> bool:
        """Verifica se está no pós-mercado (17:00 - 17:30)."""
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        if not self.is_trading_day(current_time):
            return False
        
        current_time_only = current_time.time()
        return B3_CLOSE <= current_time_only < B3_POST_CLOSE
    
    def get_trading_status(self, current_time: Optional[datetime] = None) -> str:
        """
        Retorna status atual do mercado.
        Returns: 'PRE_MARKET', 'TRADING', 'POST_MARKET', 'CLOSED'
        """
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        if not self.is_trading_day(current_time):
            return 'CLOSED'
        
        if self.is_pre_market(current_time):
            return 'PRE_MARKET'
        elif self.is_trading_hours(current_time):
            return 'TRADING'
        elif self.is_post_market(current_time):
            return 'POST_MARKET'
        else:
            return 'CLOSED'
    
    def get_next_trading_open(self, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """Retorna próxima abertura do mercado."""
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        # Se já passou das 17:00 hoje, próxima abertura é amanhã
        if current_time.time() >= B3_CLOSE:
            next_day = current_time + timedelta(days=1)
        else:
            next_day = current_time
        
        # Encontrar próximo dia útil
        while next_day.weekday() >= 5:  # Sábado ou Domingo
            next_day = next_day + timedelta(days=1)
        
        # Combinar data com horário de abertura
        return self.timezone.localize(
            datetime.combine(next_day.date(), B3_OPEN)
        )
    
    def get_today_close(self, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """Retorna fechamento do mercado hoje."""
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        if not self.is_trading_day(current_time):
            return None
        
        return self.timezone.localize(
            datetime.combine(current_time.date(), B3_CLOSE)
        )
    
    def should_start_trading(self, current_time: Optional[datetime] = None) -> bool:
        """Verifica se deve iniciar trading (pré-mercado ou abertura)."""
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        if not self.is_trading_day(current_time):
            return False
        
        current_time_only = current_time.time()
        # Inicia no pré-mercado (09:45)
        return B3_PRE_OPEN <= current_time_only < B3_CLOSE
    
    def should_stop_trading(self, current_time: Optional[datetime] = None) -> bool:
        """Verifica se deve parar trading (após fechamento)."""
        if current_time is None:
            current_time = self.get_current_b3_time()
        
        current_time_only = current_time.time()
        # Para após o fechamento (17:00)
        return current_time_only >= B3_CLOSE


# Função auxiliar para uso rápido
def is_b3_trading_hours() -> bool:
    """Verifica rapidamente se está no horário de trading da B3."""
    schedule = TradingSchedule()
    return schedule.is_trading_hours()


if __name__ == '__main__':
    # Teste
    schedule = TradingSchedule()
    now = schedule.get_current_b3_time()
    
    print(f"Horário atual (B3): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"É dia útil: {schedule.is_trading_day()}")
    print(f"Status: {schedule.get_trading_status()}")
    print(f"Horário de trading: {schedule.is_trading_hours()}")

