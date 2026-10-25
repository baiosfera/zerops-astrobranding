"""
Starter Crew 2: Google Business Profile & Local SEO Audit Crew
Features graceful degradation / feature flag for GOOGLE_MAPS_API_KEY.
"""
import os
from typing import Dict, Any
from .crew_factory import get_bifrost_llm, CrewFactory

def check_google_maps_api_key() -> bool:
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    return bool(key)

def create_google_seo_crew(topic: str, context: Dict[str, Any] = None, tier: str = "pro"):
    try:
        from crewai import Agent, Task, Crew, Process
    except ImportError:
        raise RuntimeError("crewai is not installed")

    llm = get_bifrost_llm(tier=tier)
    has_api_key = check_google_maps_api_key()

    auditor_backstory = (
        "Sos un auditor de presencia digital y SEO local especializado en Google Business Profile y Google Maps. "
        "Evaluás completitud de ficha (NAP: Nombre, Dirección, Teléfono), fotos, servicios y consistencia."
    )
    if not has_api_key:
        auditor_backstory += (
            " NOTA OPERATIVA: La variable GOOGLE_MAPS_API_KEY no está inyectada en el servidor. "
            "Debés advertir claramente al usuario sobre la falta de la clave API para consultas en vivo, "
            "y proceder a generar la guía estratégica de auditoría basada en los datos proporcionados en el contexto."
        )

    auditor = Agent(
        role="Auditor de Google Business y Presencia Local",
        goal=f"Analizar la presencia local del negocio: '{topic}' y detectar inconsistencias o áreas de mejora.",
        backstory=auditor_backstory,
        llm=llm,
        verbose=False
    )

    reputation_agent = Agent(
        role="Especialista en Reputación y Respuestas a Reseñas",
        goal="Generar estrategias de respuesta a opiniones de clientes (positivas y negativas) y propuestas de optimización de perfil.",
        backstory="Sos un experto en relaciones públicas y conversión local que redacta respuestas empáticas y optimizadas con palabras clave locales.",
        llm=llm,
        verbose=False
    )

    t1 = Task(
        description=(
            f"Auditar la ficha y presencia de: '{topic}'. "
            f"Si falta la API de Google en vivo, generar el checklist de verificación y diagnóstico paso a paso."
        ),
        expected_output="Informe de diagnóstico de presencia local con verificación de NAP, categorías y fotos.",
        agent=auditor
    )

    t2 = Task(
        description="Redactar el plan de acción para mejorar el posicionamiento en Google Maps y 3 plantillas de respuesta a reseñas frecuentes.",
        expected_output="Plan de acción SEO local en Markdown con plantillas de respuesta a reseñas y palabras clave recomendadas.",
        agent=reputation_agent
    )

    return Crew(
        agents=[auditor, reputation_agent],
        tasks=[t1, t2],
        process=Process.sequential,
        verbose=False
    )

CrewFactory.register("google_seo", create_google_seo_crew)
CrewFactory.register("seo_local", create_google_seo_crew)
