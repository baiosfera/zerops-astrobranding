"""
Dynamic Crew Factory & Unified Bifrost LLM Provider
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("hermes.crew_factory")

BIFROST_URL = os.getenv("HERMES_MODEL_ENDPOINT", "http://bifrost:8080/v1")
BIFROST_VK = os.getenv("BIFROST_VK_CREWAI", os.getenv("BIFROST_VIRTUAL_KEY", "vk-crewai"))

def get_bifrost_llm(tier: str = "free"):
    """
    Returns a configured CrewAI LLM pointing to the Bifrost Gateway.
    - tier 'free': Routes to FreeLLMAPI ($0) via Bifrost rule 1.
    - tier 'pro': Injects x-routing-tier: pro to route directly to DeepSeek via Bifrost CEL priority 0.
    """
    try:
        from crewai import LLM
    except ImportError:
        logger.warning("crewai not installed in current environment.")
        return None

    if tier == "pro":
        model_name = "openai/deepseek-chat"
        extra_headers = {"x-routing-tier": "pro", "x-tier": "production"}
    else:
        model_name = "openai/hermes-3-llama-3.1-8b"
        extra_headers = {"x-routing-tier": "free"}

    return LLM(
        model=model_name,
        base_url=BIFROST_URL,
        api_key=BIFROST_VK,
        temperature=0.3,
        extra_headers=extra_headers
    )

class CrewFactory:
    _registry: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, builder_fn):
        cls._registry[name.lower()] = builder_fn
        logger.info(f"Registered Crew in factory: {name}")

    @classmethod
    def list_crews(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    def execute(cls, crew_name: str, topic: str, context: Optional[Dict[str, Any]] = None, tier: str = "free") -> str:
        key = crew_name.lower().strip()
        if key not in cls._registry:
            available = ", ".join(cls._registry.keys())
            return f"Error: Crew '{crew_name}' no existe. Equipos disponibles: {available}"
        
        builder = cls._registry[key]
        crew_instance = builder(topic=topic, context=context or {}, tier=tier)
        try:
            result = crew_instance.kickoff()
            return str(result)
        except Exception as e:
            logger.error(f"Error executing crew '{crew_name}': {e}")
            return f"Error ejecutando cuadrilla {crew_name}: {str(e)}"

    @classmethod
    def create_dynamic_crew(cls, goal: str, roles: List[Dict[str, str]], tier: str = "free") -> str:
        """
        Dynamically assembles an ad-hoc Crew from natural language roles.
        roles: [{"role": "Investigador", "goal": "Buscar datos", "backstory": "..."}]
        """
        try:
            from crewai import Agent, Task, Crew, Process
        except ImportError:
            return "Error: crewai no está disponible en este entorno."

        llm = get_bifrost_llm(tier=tier)
        agents = []
        tasks = []

        for idx, r in enumerate(roles):
            agent = Agent(
                role=r.get("role", f"Especialista {idx+1}"),
                goal=r.get("goal", goal),
                backstory=r.get("backstory", f"Experto enfocado en {goal}"),
                llm=llm,
                verbose=False
            )
            agents.append(agent)
            task = Task(
                description=f"Contribuir al objetivo general: '{goal}'. Enfoque específico: {r.get('role')}.",
                expected_output="Resumen ejecutivo estructurado con hallazgos y recomendaciones.",
                agent=agent
            )
            tasks.append(task)

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=False
        )

        try:
            output = crew.kickoff()
            return str(output)
        except Exception as e:
            return f"Error en ejecución de cuadrilla dinámica: {str(e)}"
