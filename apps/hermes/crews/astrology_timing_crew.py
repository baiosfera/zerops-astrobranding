"""
Starter Crew 3: Astrological Timing & Natal Synthesis Crew
Connects mathematical calculations with high-converting narrative interpretations.
"""
from typing import Dict, Any
from .crew_factory import get_bifrost_llm, CrewFactory

def create_astrology_timing_crew(topic: str, context: Dict[str, Any] = None, tier: str = "pro"):
    try:
        from crewai import Agent, Task, Crew, Process
    except ImportError:
        raise RuntimeError("crewai is not installed")

    llm = get_bifrost_llm(tier=tier)

    astro_tech = Agent(
        role="Astrónomo / Analista Técnico de Efemérides",
        goal=f"Analizar las posiciones planetarias, aspectos y tránsitos para la consulta: '{topic}'.",
        backstory="Sos un matemático y calculador astrológico riguroso que trabaja exclusivamente con datos astronómicos verificados y posiciones exactas.",
        llm=llm,
        verbose=False
    )

    narrative_agent = Agent(
        role="Intérprete Humanista y Redactor de Diagnósticos",
        goal="Convertir los datos técnicos de la carta o tránsito en un diagnóstico psicológico y de timing aplicable a la vida real.",
        backstory="Sos un astrólogo humanista con 20 años de experiencia que traduce aspectos planetarios complejos en orientación práctica y comprensible.",
        llm=llm,
        verbose=False
    )

    t1 = Task(
        description=f"Examinar los factores astronómicos y de timing asociados a: '{topic}'. Resumir aspectos mayores, casas y planetas regentes.",
        expected_output="Dossier técnico de factores astrológicos y tránsitos clave.",
        agent=astro_tech
    )

    t2 = Task(
        description="Redactar el diagnóstico personalizado final en un tono cálido, profundo y libre de fatalismo o jerga incomprensible.",
        expected_output="Informe de diagnóstico astrológico en Markdown con fortalezas, áreas de atención y fechas clave.",
        agent=narrative_agent
    )

    return Crew(
        agents=[astro_tech, narrative_agent],
        tasks=[t1, t2],
        process=Process.sequential,
        verbose=False
    )

CrewFactory.register("astrology", create_astrology_timing_crew)
CrewFactory.register("astrologia", create_astrology_timing_crew)
