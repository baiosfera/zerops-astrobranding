"""
Sovereign SEO, AEO & GEO Crew (v2.0 SOTA)
Hydrates CoHaLo Hard Rules, Schema.org RDF @graph, llms.txt v2,
and OpenGraph WhatsApp <300KB budget from the sovereign seo-aeo-geo skill.
"""
import os
import logging
from typing import Dict, Any, Optional
from .crew_factory import get_bifrost_llm, CrewFactory
from .universal_harness import UniversalSkillHarness

logger = logging.getLogger("hermes.crews.seo_aeo_geo")

def create_seo_aeo_geo_crew(topic: str, context: Optional[Dict[str, Any]] = None, tier: str = "free"):
    """
    Creates a dedicated 2-agent CrewAI team for SEO/AEO/GEO optimization of any digital brand or storefront.
    Runs on Bifrost -> FreeLLMAPI ($0 pool) by default.
    """
    try:
        from crewai import Agent, Task, Crew, Process
    except ImportError:
        raise RuntimeError("crewai is not installed in the current environment.")

    llm = get_bifrost_llm(tier=tier)
    spec = UniversalSkillHarness.get_skill("seo-aeo-geo")

    # Agent 1: Search, Answer & Generative Engine Optimization Architect
    aeo_architect = Agent(
        role="Arquitecto Soberano SEO, AEO & GEO",
        goal=f"Modelar el Knowledge Graph RDF @graph de Schema.org, endpoint llms.txt y optimizar visibilidad para '{topic}' en Google, SearchGPT y Perplexity.",
        backstory=(
            f"Sos el arquitecto líder en Search & Answer Engine Optimization.\n"
            f"Tu misión es posicionar marcas en motores tradicionales y motores generativos (ChatGPT, Perplexity, Claude).\n"
            f"REGLAS INVIOLABLES DE DOMINIO:\n"
            f"{spec.hard_rules}\n\n"
            f"Garantizás Schema.org unificado en un solo script con RDF @graph, sub-1.0s LCP y cero CLS."
        ),
        llm=llm,
        tools=[UniversalSkillHarness.create_skill_reference_tool(spec)],
        verbose=False
    )

    # Agent 2: Visual Assets & Multi-Surface Social Graph Engineer
    visual_engineer = Agent(
        role="Ingeniero de Activos Visuales & Redirecciones Edge",
        goal=f"Verificar tarjetas OpenGraph 1200x630 bajo el presupuesto estricto de WhatsApp (<300KB), zona segura 1080x600 y suite de favicons.",
        backstory=(
            f"Sos el ingeniero especialista en metadatos visuales y entrega en el edge.\n"
            f"Controlás que ninguna imagen compartida en WhatsApp falle por superar los 300KB.\n"
            f"Verificás que la tipografía y logos vivan dentro de la safe zone 1080x600 y que los redirects HTTP a HTTPS se apliquen en Cloudflare Edge."
        ),
        llm=llm,
        tools=[UniversalSkillHarness.create_skill_reference_tool(spec)],
        verbose=False
    )

    # Task 1: Knowledge Graph & AEO Analysis
    task_knowledge_graph = Task(
        description=(
            f"Analizar el dominio y catálogo de '{topic}'.\n"
            f"1. Generar la estructura JSON-LD Schema.org completa con RDF @graph para la marca (LocalBusiness/Store, Product, Offer, AggregateRating).\n"
            f"2. Formular la especificación del archivo /llms.txt y /llms-full.txt para indexación por agentes de IA.\n"
            f"3. Definir palabras clave y respuestas concisas para Answer Engine Optimization (Perplexity/SearchGPT)."
        ),
        expected_output="Especificación JSON-LD Schema.org (@graph), contenido para llms.txt y estrategia AEO estructurada en Markdown.",
        agent=aeo_architect
    )

    # Task 2: Multi-Surface Visual & Edge Audit
    task_visual_edge = Task(
        description=(
            f"Auditar la entrega visual y reglas de borde para '{topic}'.\n"
            f"1. Validar las etiquetas OpenGraph y Twitter Card (1200x630, safe zone 1080x600).\n"
            f"2. Aplicar el presupuesto estricto de WhatsApp (<300KB) en imágenes de vista previa.\n"
            f"3. Definir las reglas de redirección 301 canónicas en Cloudflare Edge (HTTP a HTTPS y no-www a www)."
        ),
        expected_output="Auditoría de activos visuales OpenGraph (<300KB), safe zone, suite de favicons y reglas Edge en Markdown.",
        agent=visual_engineer
    )

    return Crew(
        agents=[aeo_architect, visual_engineer],
        tasks=[task_knowledge_graph, task_visual_edge],
        process=Process.sequential,
        verbose=False
    )

# Register in factory under canonical slugs
CrewFactory.register("seo_aeo_geo", create_seo_aeo_geo_crew)
CrewFactory.register("seo-aeo-geo", create_seo_aeo_geo_crew)
CrewFactory.register("seo", create_seo_aeo_geo_crew)
CrewFactory.register("google_seo", create_seo_aeo_geo_crew)
