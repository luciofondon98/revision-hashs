import streamlit as st
import pandas as pd
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO

# Función para leer los hashes del archivo txt subido
def get_hashes(file):
    hashes = []
    stringio = StringIO(file.getvalue().decode("utf-8"))
    for linea in stringio:
        hashes.append(linea.strip())  # strip() elimina espacios en blanco adicionales alrededor de la línea
    return hashes

def translate_hash(hash):
    pixel_url='pixel.retargeting.cl'
    origin='jetsmart.com'   
    
    headers = {
        "Origin": origin,
        "rtID": "++++++++JET++++++SMART___3",
        "rtS": "++++++++JET++++++SMART___3",
        "rtV": "2"
    }
    
    url = f"https://{pixel_url}/promo/{hash[:3]}/validate"
    response = requests.post(url, headers=headers, data=hash)
    response_data = json.loads(response.text)
    
    return response_data

# Interfaz en Streamlit
st.title("Validador de Hashes")

# Subida del archivo .txt
uploaded_file = st.file_uploader("Sube tu archivo .txt con los hashes", type="txt")

# Verifica si se subió el archivo
if uploaded_file is not None:
    st.write("Archivo cargado exitosamente. Procesando...")

    # Lee los hashes del archivo
    hashes = get_hashes(uploaded_file)

    # Muestra los primeros 5 hashes
    st.write("Primeros 5 hashes procesados:", hashes[:5])

    # Inicializa el diccionario para almacenar resultados
    results_dict = {}

    # Usamos ThreadPoolExecutor para hacer las llamadas concurrentes
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_value = {executor.submit(translate_hash, hash): hash for hash in hashes}
        
        for future in as_completed(future_to_value):
            value = future_to_value[future]
            try:
                # Recoge el resultado de la API
                resultado = future.result()
                results_dict[resultado['value']] = resultado['success']
            except Exception as e:
                st.write(f'Error fetching {value}: {e}')

    # Invertimos los valores de éxito para que sean más comprensibles
    results_dict_fix = {key: not value for key, value in results_dict.items()}

    # Creamos un DataFrame para los resultados
    df = pd.DataFrame(list(results_dict_fix.items()), columns=['Hash', 'Usado'])

    # Muestra la tabla de resultados
    st.write("Resultados:", df)

    # Botón para descargar los resultados como archivo Excel
    if not df.empty:
        @st.cache_data
        def convert_df_to_excel(df):
            output = StringIO()
            df.to_excel(output, index=False, engine='openpyxl')
            processed_data = output.getvalue()
            return processed_data

        excel_data = convert_df_to_excel(df)
        
        st.download_button(label="Descargar resultados en Excel", data=excel_data, file_name='resultados.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
