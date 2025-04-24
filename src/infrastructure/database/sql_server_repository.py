import pyodbc
from datetime import date
from typing import List, Optional
from src.domain.interfaces.database_repository import DatabaseRepository
from .connection import create_db_connection
import logging


logger = logging.getLogger(__name__)

class SqlServerRepository(DatabaseRepository):
    def get_lote_id(self, aviario_id: int, count_date: date) -> Optional[int]:
        conn = create_db_connection()
        if not conn:
            print("Failed to connect to database")
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT lote_id FROM prm_pro_registroDiario_00 "
                "WHERE fecha = ? AND avi_id = ?",
                count_date, aviario_id
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting lote_id: {e}")
            return None
        finally:
            conn.close()

    def upsert_egg_counts(self, aviario_id: int, count_date: date, counts: List[int], fila_mapping: dict) -> bool:
        conn = create_db_connection()
        if not conn:
            print("Failed to connect to database")
            return False
        lote_id = self.get_lote_id(aviario_id, count_date)
        if not lote_id:
            print(f"No lote_id found for aviario {aviario_id} on date {count_date}")
            return False
        success = True
        try:
            cursor = conn.cursor()
            sql = """
            DECLARE @tipo INT
            DECLARE @mensaje NVARCHAR(255)
            EXEC dbo.sp_insertar_actualizar_regdia_huevos_orion
                @rghuevos_id = NULL,
                @rghuevos_fecha = ?,
                @rghuevos_id_lote = ?,
                @rghuevos_id_aviario = ?,
                @rghuevos_fila = ?,
                @rghuevos_orion = ?,
                @tipo = @tipo OUTPUT,
                @mensaje = @mensaje OUTPUT
            SELECT @tipo AS tipo, @mensaje AS mensaje
            """
            for index, count in enumerate(counts):
                fila = fila_mapping[index]
                #print(f"Executing for fila {fila}: date={count_date}, lote_id={lote_id}, aviario_id={aviario_id}, count={count}")
                try:
                    cursor.execute(sql, count_date, lote_id, aviario_id, fila, count)
                    while cursor.description is None and cursor.nextset():
                        pass
                    result = cursor.fetchone()
                    if result:
                        tipo, mensaje = result
                        if tipo == 1:
                            pass
                            #print(f"Success for fila {fila}: {mensaje}")
                        else:
                            print(f"Error for fila {fila}: {mensaje}")
                            success = False
                    else:
                        print(f"No output received for fila {fila}")
                        success = False
                    conn.commit()
                except pyodbc.Error as e:
                    print(f"Database error for fila {fila}: {e}")
                    conn.rollback()
                    success = False
            logging.info(f"Egg counts upserted successfully for aviario {aviario_id} on date {count_date}")
            return success
        except Exception as e:
            print(f"Unexpected error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
