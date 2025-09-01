
import base64
import datetime
import os
import pytz
from flask import current_app, url_for
from ..models import Checkin, User
from ..repositories.checkin_repository import CheckinRepository
from ..repositories.user_repository import UserRepository

class CheckinService:
    def __init__(self):
        self.checkin_repo = CheckinRepository()
        self.user_repo = UserRepository()

    def get_user_checkins_today(self, user_id: int) -> list[Checkin]:
        peru_tz = pytz.timezone('America/Lima')
        today_peru = datetime.datetime.now(peru_tz).date()
        return self.checkin_repo.get_by_user_id_and_date(user_id, today_peru)

    def get_dashboard_data(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)
        peru_tz = pytz.timezone('America/Lima')
        now_peru = datetime.datetime.now(peru_tz)
        today_peru = now_peru.date()
        
        # --- CÁLCULO DE ESTADÍSTICAS ---
        primer_dia_mes = today_peru.replace(day=1)
        checkins_mes = self.checkin_repo.get_checkins_for_month(user_id, primer_dia_mes)
        
        dias_puntuales = 0
        dias_tarde = 0
        for checkin in checkins_mes:
            if checkin.status == 'A Tiempo':
                dias_puntuales += 1
            elif checkin.status == 'Tardanza':
                dias_tarde += 1

        # --- ESTADO ACTUAL DE MARCACIÓN ---
        checkin_ingreso_hoy = self.checkin_repo.get_by_user_id_and_type_and_date(user_id, 'Ingreso', today_peru)
        checkin_inicio_almuerzo_hoy = self.checkin_repo.get_by_user_id_and_type_and_date(user_id, 'Inicio Almuerzo', today_peru)
        checkin_fin_almuerzo_hoy = self.checkin_repo.get_by_user_id_and_type_and_date(user_id, 'Fin Almuerzo', today_peru)
        checkin_salida_hoy = self.checkin_repo.get_by_user_id_and_type_and_date(user_id, 'Salida', today_peru)

        proximo_tipo_marcacion = 'Ingreso'
        if checkin_ingreso_hoy:
            proximo_tipo_marcacion = 'Inicio Almuerzo'
        if checkin_inicio_almuerzo_hoy:
            proximo_tipo_marcacion = 'Fin Almuerzo'
        if checkin_fin_almuerzo_hoy:
            proximo_tipo_marcacion = 'Salida'
        if checkin_salida_hoy:
            proximo_tipo_marcacion = 'Finalizado'

        checkins_today = self.get_user_checkins_today(user_id)

        return {
            'user': user,
            'checkins': checkins_today,
            'dias_puntuales': dias_puntuales,
            'dias_tarde': dias_tarde,
            'dias_almuerzo_extendido': 0, # Lógica a implementar
            'horas_extras_mes': 0, # Se calculará en otro servicio
            'proximo_tipo_marcacion': proximo_tipo_marcacion
        }

    def perform_checkin(self, user_id: int, checkin_data: dict) -> tuple[dict | None, str, int]:
        lat = checkin_data.get('lat')
        lon = checkin_data.get('lon')
        img_data_url = checkin_data.get('img')
        tipo_marcacion = checkin_data.get('tipo')

        if not all([lat, lon, img_data_url, tipo_marcacion]):
            return None, 'Faltan datos', 400

        user = self.user_repo.get_by_id(user_id)
        peru_tz = pytz.timezone('America/Lima')
        timestamp_utc = datetime.datetime.utcnow()
        now_peru = timestamp_utc.replace(tzinfo=pytz.utc).astimezone(peru_tz)
        
        status = ''
        
        if tipo_marcacion == 'Ingreso':
            hora_limite_puntual = now_peru.replace(hour=user.horario.hora_entrada.hour, minute=user.horario.hora_entrada.minute + 5, second=59, microsecond=999999)
            status = 'A Tiempo' if now_peru.time() <= hora_limite_puntual.time() else 'Tardanza'
        
        elif tipo_marcacion == 'Inicio Almuerzo':
            status = 'Inicio Almuerzo'
            if not (user.horario.hora_inicio_almuerzo <= now_peru.time() <= user.horario.hora_fin_almuerzo):
                status = 'Inicio Almuerzo (Fuera de Horario)'

        elif tipo_marcacion == 'Fin Almuerzo':
            status = 'Fin Almuerzo'

        elif tipo_marcacion == 'Salida':
            status = 'Salida' if now_peru.time() >= user.horario.hora_salida else 'Salida (Antes de hora)'

        # --- GUARDAR FOTO ---
        try:
            img_str = img_data_url.split(',')[1]
            img_bytes = base64.b64decode(img_str)
            filename = f"{user_id}_{timestamp_utc.strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(img_bytes)
        except Exception as e:
            return None, f'Error al guardar la imagen: {e}', 500

        # --- GUARDAR EN BD ---
        new_checkin = Checkin(
            user_id=user_id,
            timestamp_utc=timestamp_utc,
            latitude=lat,
            longitude=lon,
            photo_filename=filename,
            status=status,
            tipo=tipo_marcacion
        )
        self.checkin_repo.add(new_checkin)
        self.checkin_repo.commit()

        return {
            'status': 'success',
            'message': f'Marcación de {tipo_marcacion} registrada con éxito.',
            'checkin': {
                'time': new_checkin.timestamp_peru.strftime('%H:%M:%S'),
                'status': new_checkin.status,
                'tipo': new_checkin.tipo,
                'photo_url': url_for('main.uploaded_file', filename=new_checkin.photo_filename)
            }
        }, 'Checkin successful', 200
