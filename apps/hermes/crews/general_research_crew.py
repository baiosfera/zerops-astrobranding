"""
Starter Crew 1: General Research & Executive Synthesis Crew
100% General-purpose for market research, comparative analysis, or deep dives.
"""
from typing import Dict, Any
from .crew_factory import get_bifrost_llm, CrewFactory

def create_general_research_crew(topic: str, context: Dict[str, Any] = None, tier: str = "free"):
    try:
        from crewai import Agent, Task, Crew, Process
    except ImportError:
        raise RuntimeError("crewai is not installed")

    llm = get_bifrost_llm(tier=tier)

    researcher = Agent(
        role="Investigador Principal",
        goal=f"Analizar a fondo el tema: '{topic}' y recopilar los datos más relevantes, hechos y tendencias.",
        backstory="Sos un analista de investigación senior con más de 10 años de experiencia extrayendo conclusiones críticas de múltiples fuentes objetivas.",
        llm=llm,
        verbose=False
    )

    synthesizer = Agent(
        role="Estratega de Síntesis y Redactor Ejecutivo",
        goal="Transformar los hallazgos de investigación en un informe ejecutivo claro, procesable y estructurado.",
        backstory="Sos un consultor de estrategia que comunica conclusiones complejas con lenguaje directo, viñetas de impacto y próximos pasos.",
        llm=llm,
        verbose=False
    )

    t1 = Task(
        description=f"Investigar exhaustivamente sobre: '{topic}'. Identificar patrones clave, ventajas, desventajas y datos de contexto.",
        expected_output="Dossier de investigación con puntos clave y análisis de fondo.",
        agent=researcher
    )

    t2 = Task(
        description="Revisar el dossier de investigación y redactar el informe ejecutivo final con recomendaciones concretas.",
        expected_output="Informe ejecutivo en Markdown con resumen, hallazgos principales, riesgos y recomendaciones.",
        agent=synthesizer
    )

    return Crew(
        agents=[researcher, synthesizer],
        tasks=[t1, t2],
        process=Process.sequential,
        verbose=False
    )

CrewFactory.register("general_research", create_general_research_crew)
CrewFactory.register("investigacion", create_general_research_crew)
