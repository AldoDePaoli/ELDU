import streamlit as pd
import streamlit as st
from google import genai
from google.genai import types

# 1. CONFIGURACIÓN DE LA PÁGINA (Diseño amigable y limpio)
st.set_page_config(
    page_title="Validador Experto: Ley de Urgencia Chile",
    page_icon="🩺",
    layout="wide",
)

# Estilo visual mejorado
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #007bff; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)


# 2. INICIALIZACIÓN DE LA API DE GEMINI
# Primero intenta buscar la clave oculta en internet (Secrets)
api_key = st.secrets.get("GEMINI_API_KEY", None)

# Si no la encuentra (como cuando pruebas en tu PC), la pide en pantalla
if not api_key:
    st.sidebar.markdown("### 🔑 Autenticación")
    api_key = st.sidebar.text_input("Ingresa tu Gemini API Key:", type="password")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    st.info("👈 Por favor, ingresa tu Gemini API Key en la barra lateral para comenzar.")
    st.stop()

# 3. PROMPT DEL SISTEMA (El cerebro médico-legal)
SYSTEM_INSTRUCTION = """
Eres un médico auditor experto en la legislación sanitaria chilena y la Ley de Urgencia (Ley Nº 19.650 / Decreto Supremo Nº 369).
Tu tarea es evaluar si el caso cumple estrictamente con el beneficio de "Urgencia Vital o Secuela Funcional Grave Impostergable".

REGLAS DE EVALUACIÓN ESTRICTA (NORMATIVA CHILENA Y CRITERIOS REALES):
Para que sea Ley de Urgencia, el paciente debe presentar una condición de riesgo vital inminente o riesgo de secuela grave si no se interviene INMEDIATAMENTE. No basta con que requiera hospitalización.

Aplica estrictamente los siguientes criterios de corte:

1. INSUFICIENCIA RESPIRATORIA AGUDA:
   - NO inventes criterios de FiO2 > 50%.
   - Criterio estricto: Debe haber una Insuficiencia Respiratoria Aguda de tipo Global o Catastrófica (PaO2 < 60 mmHg y/o PaCO2 > 50 mmHg respirando aire ambiental, o necesidad inmediata de Ventilación Mecánica Invasiva o No Invasiva, o signos francos de claudicación respiratoria con uso de musculatura accesoria y cianosis).

2. SHOCK / SEPSIS SEVERA:
   - Criterios Surviving Sepsis (Sepsis-3): Sospecha de foco infeccioso + disfunción de órganos (aumento de 2 puntos en score SOFA o criterios qSOFA alterados).
   - Shock Séptico: Necesidad de vasopresores (Noradrenalina) para mantener PAM >= 65 mmHg Y lactato sérico > 2 mmol/L a pesar de una reanimación adecuada con fluidos.

3. CARDIOVASCULAR:
   - IAM con SDST o nuevo bloqueo de rama izquierda, arritmias ventriculares letales (TV/FV) o bradiarritmias con compromiso hemodinámico (requerimiento de marcapasos externo). Angina inestable de alto riesgo con dolor refractario.
   - Guías AHA/ESC (Infradesnivel/Supradesnivel de ST, arritmias inestables).

4. ACCIDENTE CEREBROVASCULAR (ACV):
   - ACV Isquémico o Hemorrágico agudo con déficit neurológico focal focalizado (NIHSS > 0) dentro de la ventana terapéutica o con signos de hipertensión endocraneana.

5. TRASTORNOS HIDROELECTROLÍT
   - Guías europeas/americanas (ej. Hiponatremia severa < 125 mEq/L con compromiso neurológico).

FORMATO DE RESPUESTA REQUERIDO:

# 🚨 EVALUACIÓN LEY DE URGENCIA 🚨

## ¿CUMPLE CRITERIO ESTRICTO?: [SÍ / NO]

### [Si la respuesta es SÍ]
* **Grupo de Emergencia / Categoría:** [Indica el grupo exacto del D.S. 369]
* **Numeral/Articulado Específico:** [Ej: Numeral de Insuficiencia Respiratoria Aguda o Shock]
* **Justificación Médica (Breve Definición):** [Explica en un párrafo corto usando los datos del paciente (gases, clínica) por qué cumple el criterio estricto, citando explícitamente por qué hay riesgo vital].

### [Si la respuesta es NO]
* **Razón del Rechazo:** [Explica por qué los parámetros ingresados (ej: saturación normal, gases estables, hemodinamia conservada) NO configuran una urgencia vital bajo el amparo estricto de la ley chilena, desestimando criterios incorrectos].

Mantén un tono profesional, técnico, pericial y directo. Evita ambigüedades.
"""

# 4. INTERFAZ DE USUARIO (Frontend)
st.title("🩺 Validador Inteligente de Ley de Urgencia")
st.subheader("Herramienta de apoyo pericial para Médicos de Urgencia en Chile")
st.caption(
    "Nota: Esta herramienta es un soporte basado en guías clínicas y el Decreto Nº 369. La decisión final es siempre del médico tratante."
)

st.write("---")

# Organización en dos columnas para optimizar el espacio visual
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📋 Datos del Paciente en Urgencia")

    # Campos estructurados para facilitar el ingreso ordenado
    diagnostico = st.text_input(
        "**Diagnóstico Presuntivo / Principal:**",
        placeholder="Ej: IAM con SDST de pared anterior / Shock Séptico de foco urinario",
    )

    historia_clinica = st.text_area(
        "**Historia Clínica, Examen Físico, Laboratorio e Imágenes:**",
        placeholder="Copia y pega el ingreso de urgencia aquí...\nEjemplo:\n- Anamnesis: Paciente de 65 años con dolor opresivo irradiado a brazo izquierdo de 2 horas de evolución.\n- Examen Físico: Diaforético, PA 90/60, FC 110 lpm.\n- ECG: Supradesnivel del segmento ST de 3mm en V1-V4.\n- Lab: Troponinas ultrasensibles elevadas.",
        height=350,
    )

    procesar_boton = st.button("🚀 Evaluar Criterio de Ley de Urgencia")

with col2:
    st.markdown("### ⚖️ Dictamen Pericial de IA")

    if procesar_boton:
        if not diagnostico or not historia_clinica:
            st.warning(
                "⚠️ Por favor, completa el diagnóstico y la historia clínica antes de evaluar."
            )
        else:
            with st.spinner("Analizando antecedentes frente al Decreto Supremo..."):
                try:
                    # Construcción del prompt unificado para el modelo
                    user_content = f"""
                    DIAGNÓSTICO ANOTADO: {diagnostico}
                    
                    ANTECEDENTES CLÍNICOS (HISTORIA, EF, LABS, IMÁGENES, ECG):
                    {historia_clinica}
                    """

                    # Llamada oficial a la SDK de Google GenAI usando Gemini 2.5 Flash
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=user_content,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.1,  # Temperatura baja para respuestas consistentes y precisas
                        ),
                    )

                    # Mostrar el cuadro de respuesta de forma limpia
                    st.success("Análisis finalizado con éxito.")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"Ocurrió un error al conectar con Gemini: {e}")
    else:
        st.info(
            "⬅️ Completa los datos de la izquierda y haz clic en el botón para generar el informe médico-legal."
        )

st.write("---")
st.caption(
    "Desarrollado para la Red de Urgencia Pública y Privada de Chile. Software de distribución gratuita."
)