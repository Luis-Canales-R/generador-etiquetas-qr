import csv
import sqlite3
from pathlib import Path

print("--- INICIANDO SCRIPT DE IMPORTACIÓN ---")

try:
    # --- Hacemos la ruta inteligente ---
    BASE_DIR = Path(__file__).resolve().parent
    DB_FILE = BASE_DIR / 'data' / 'products.db'
    CSV_FILE = BASE_DIR / 'data' / 'import_products.csv'

    print(f"Directorio base del script: {BASE_DIR}")
    print(f"Ruta a la base de datos: {DB_FILE}")
    print(f"Ruta al archivo CSV: {CSV_FILE}")

    if not CSV_FILE.exists():
        print("\n!!! ERROR FATAL: No se encuentra el archivo 'import_products.csv' en la carpeta 'data'.")
        exit() # Detiene el script

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("\nConexión a la base de datos exitosa.")
    print("Leyendo archivo CSV...")

    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file, delimiter=';')
        
        # Imprimimos los encabezados que el lector encontró en el CSV
        print(f"Encabezados encontrados en el CSV: {csv_reader.fieldnames}\n")

        imported_count = 0
        for row in csv_reader:
            try:
                # Nombres de columna que esperamos (asegúrate que coinciden con los que imprimió arriba)
                inventory_number = row['ActivoFijo']
                serial_number = row['NumeroSerie']
                product_name = row['Equipo']
                brand = row['Marca']
                model = row['Modelo']
                equipment_type = row['TipoEquipo']

                cursor.execute("""
                    INSERT INTO products (
                        inventory_number, product_name, serial_number, brand, model, equipment_type
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (inventory_number, product_name, serial_number, brand, model, equipment_type))
                
                imported_count += 1

            except KeyError as e:
                print(f"  - !!! ERROR DE COLUMNA: No se encontró la columna {e}. Revisa los encabezados.")
                break # Detenemos el bucle al primer error de columna
            except sqlite3.IntegrityError:
                print(f"  - OMITIDO (ya existe): {row['Equipo']} ({row['ActivoFijo']})")
            except Exception as e:
                print(f"  - ERROR en la fila {row}: {e}")

    conn.commit()
    conn.close()

    print(f"\nSe intentaron importar {imported_count} productos.")
    print("¡Importación completada!")

except Exception as e:
    print(f"\n!!! Ocurrió un error general en el script: {e}")