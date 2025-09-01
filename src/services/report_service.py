
import datetime
from ..models import User, Checkin, HorasExtras, DiaDescanso
from ..repositories.user_repository import UserRepository
from ..repositories.checkin_repository import CheckinRepository
from ..repositories.horas_extras_repository import HorasExtrasRepository
from ..repositories.dia_descanso_repository import DiaDescansoRepository

class ReportService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.checkin_repo = CheckinRepository()
        self.horas_extras_repo = HorasExtrasRepository()
        self.dia_descanso_repo = DiaDescansoRepository()

    def get_admin_dashboard_summary(self) -> list[dict]:
        users = self.user_repo.get_all()
        summary_data = []
        today = datetime.date.today()
        start_of_month = today.replace(day=1)

        for user in users:
            total_lateness = self.checkin_repo.count_lateness_for_month(user.id, start_of_month)
            total_overtime = self.horas_extras_repo.get_total_for_month(user.id, today.strftime('%Y-%m'))
            worked_days = self.checkin_repo.count_worked_days_for_month(user.id, start_of_month)
            
            total_absences = 0 # Implement a more robust logic if necessary

            summary_data.append({
                'user': user,
                'total_lateness': total_lateness,
                'total_overtime': round(total_overtime, 2),
                'total_absences': total_absences
            })
        return summary_data

    def generate_report(self, user_id: int | None, start_date: datetime.date, end_date: datetime.date) -> list[dict]:
        if user_id:
            users = [self.user_repo.get_by_id(user_id)]
        else:
            users = self.user_repo.get_all()

        report_data = []
        dias_es = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        
        for user in users:
            user_data = {'user': user, 'days': []}
            current_date = start_date
            while current_date <= end_date:
                day_data = {
                    'date': current_date,
                    'dia_semana': dias_es[current_date.strftime('%A')],
                    'check_in': None, 'lunch_start': None, 'lunch_end': None,
                    'lunch_duration': None, 'check_out': None, 'overtime': None,
                    'absence': False, 'day_off': False
                }

                if self.dia_descanso_repo.get_by_user_id_and_date(user.id, current_date):
                    day_data['day_off'] = True
                else:
                    checkins_today = self.checkin_repo.get_by_user_id_and_date(user.id, current_date)

                    if not checkins_today and current_date.weekday() < 5: # Assume absence only on weekdays
                        day_data['absence'] = True
                    else:
                        for checkin in checkins_today:
                            if checkin.tipo == 'Ingreso': day_data['check_in'] = checkin
                            elif checkin.tipo == 'Inicio Almuerzo': day_data['lunch_start'] = checkin
                            elif checkin.tipo == 'Fin Almuerzo': day_data['lunch_end'] = checkin
                            elif checkin.tipo == 'Salida': day_data['check_out'] = checkin
                    
                        if day_data['lunch_start'] and day_data['lunch_end']:
                            duration = day_data['lunch_end'].timestamp_utc - day_data['lunch_start'].timestamp_utc
                            day_data['lunch_duration'] = str(duration).split('.')[0]

                    overtime = self.horas_extras_repo.get_by_user_id_and_date(user.id, current_date)
                    if overtime: day_data['overtime'] = overtime.horas

                user_data['days'].append(day_data)
                current_date += datetime.timedelta(days=1)
                
            report_data.append(user_data)

        return report_data
