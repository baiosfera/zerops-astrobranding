# 🎓 Manual del Estudiante: Domina Cualquier Curso con NotebookLM Pro y NLM-Tutor (v4.0.0)

¡Bienvenido a tu nuevo sistema de estudio de alto rendimiento! Este sistema fue diseñado especialmente para vos: no necesitás saber nada de programación ni lidiar con configuraciones complejas.

Combina las mejores técnicas comprobadas por la ciencia del aprendizaje acelerado y la dinámica de sistemas:
- **Recuerdo Activo (*Active Recall*)**: Práctica de recuperación a libro cerrado para quebrar la "ilusión de fluidez" (creer que sabemos algo solo porque lo leímos de forma pasiva).
- **Indagación Causal Progresiva**: Enfoque socrático de razonamiento de causas, efectos y consecuencias de segundo orden en lugar de memorización de definiciones.
- **Deconstrucción 80/20**: Identificación del núcleo de principios que aportan el 80% del valor práctico y funcional de la materia.
- **Repetición Espaciada Científica**: Cronograma matemático de repasos para transferir el conocimiento a la memoria de largo plazo sin relecturas inútiles.
- **Tutor Socrático NotebookLM**: Acompañamiento socrático riguroso y personalizado, anclado al 100% en las fuentes de tu cuaderno.
- **Arquitectura Python Nativa**: Comunicación directa mediante el SDK de `notebooklm_tools.services` (0 subprocesos shell, 0 tokens de API externa).

> [!IMPORTANT]
> **Cero espacio en tu computadora**: Este sistema opera 100% en la nube dentro de tu cuenta de Google NotebookLM Pro (Google One 5TB). Nada se descarga en tu disco local.

---

## 🚀 Paso 1: Configurar un Cuaderno con 1 Solo Comando

Cuando subas un nuevo curso o material a Google NotebookLM (mediante `mcv-download --upload-nlm` o manualmente), abrí tu terminal y ejecutá:

```bash
nlm-tutor setup "Nombre o ID de tu Cuaderno"
```

*(Si no recordás el nombre exacto, ejecutá `nlm-tutor list` para ver todos tus cuadernos).*

Podés configurar el cuaderno de forma automática (adaptación semántica de dominio) o seleccionar un perfil:
- `nlm-tutor setup <ID>`: Detección semántica automática del dominio (monotemático enfocado vs multidominio vs macro-currículum) y protección de cuota Google One.
- `nlm-tutor setup <ID> --profile core`: Suite esencial y rápida (8-10 artefactos nucleares).
- `nlm-tutor setup <ID> --profile standard`: Suite completa integral de estudio.
- `nlm-tutor setup <ID> --profile exhaustive`: Suite macro-curricular para grandes colecciones documentales.
- `nlm-tutor setup <ID> --with-video`: Genera además video explicativo en Studio (por defecto omitido para proteger la cuota de 5 horas de Google One).
- `nlm-tutor setup <ID> --all-media`: Genera todas las modalidades de audio (brief, deep_dive, critique, debate) y video.
- `nlm-tutor setup <ID> --no-media`: Genera exclusivamente entregables de texto, mapas y visuales (consumo: 0% cuota multimedia).

> [!TIP]
> **Disponibilidad Inmediata con Audio-First**: Gracias a la arquitectura Audio-First de `mcv-download` (v5.0.0) o usando la bandera `--audio-only`, los audios se extraen en Raw AAC 24k mono y se suben a NotebookLM Pro (hasta 300 fuentes) en apenas ~2 minutos. Podés ejecutar `nlm-tutor setup` de inmediato sin tener que esperar a que termine la transcodificación 360p de video.

**¿Qué hace este comando automáticamente por vos?**
1. **Verificación Previa de Cuota Google One**: Analiza tu saldo de cómputo multimedia en Google One y te alerta si queda menos del 15% para protegerte contra límites de API (`RESOURCE_EXHAUSTED`).
2. **Configura el Chat Socrático del Tutor**: Calibra a NotebookLM como tu tutor socrático que no te da respuestas fáciles ni resúmenes complacientes, sino que te hace preguntas progresivas y te ayuda a razonar.
3. **Genera la Suite Adaptativa de Artefactos**: Crea en tu panel de Studio toda la batería de audios en español latinoamericano (`es-419`), mapas, simulacros, tablas, diapositivas y guías ordenadas progresivamente sin saturar tu cuota multimedia.
4. **Persiste el Manifiesto SSoT en la Nube (Cero Basura en Disco)**: Almacena los identificadores directamente en la nota `00_RUTA_DE_ESTUDIO` dentro del cuaderno, con 0 bytes en tu disco local y portabilidad total entre dispositivos.
5. **Crea tu Cuaderno de Lagunas**: Abre una nota especial en tu cuaderno llamada `00_CUADERNO_DE_LAGUNAS` para registrar exclusivamente los puntos ciegos que necesitas reforzar.
6. **Crea tu Ruta de Estudio**: Diseña la guía paso a paso dentro del cuaderno en la nota `00_RUTA_DE_ESTUDIO`.

---

## 🗺️ Paso 2: La Suite de Artefactos Cognitivos (Tu Camino Paso a Paso)

En la columna izquierda de tu Google NotebookLM (panel de Studio) vas a encontrar los recursos numerados según tu perfil seleccionado:

| # | Artefacto Generado | ¿Para qué sirve? | ¿Cómo usarlo? |
|---|---|---|---|
| **01** | `01_DIAGNOSTICO_Activacion-Conceptual` | Micro-evaluación ágil de preguntas de selección múltiple (A, B, C) (Pre-testing formativo). | Hacelo al empezar para activar la curiosidad sin agotarte con cuestionarios largos o preguntas abiertas. |
| **02** | `02_MAPA_Syllabus-Estructural` | Vista panorámica de la red conceptual y jerarquías del tema. | Miralo 3 minutos para entender cómo se conectan los módulos y principios rectores. |
| **03** | `03_AUDIO_Inmersion-General-Podcast` | Conversación estilo podcast en español latinoamericano (`es-419`, acento divulgativo natural). | Escuchalo primero mientras ordenás tu espacio o salís a caminar. Te da una visión global amena y conectada. |
| **04** | `04_INFORME_Documento-Informativo-Briefing` | Dossier ejecutivo y briefing de fuentes con síntesis factual de alto nivel. | Tu documento de referencia rápida para ubicar qué aborda cada autor y tema. |
| **05** | `05_INFORME_Sintesis-Ejecutiva-y-Modelos` | Documento maestro con tesis central, modelos mentales y glosario operativo. | Tu texto base de consulta cuando quieras profundizar un concepto específico. |
| **06** | `06_TABLA_Matriz-Comparativa-Debates` | Matriz de contrastes, trade-offs y controversias entre enfoques. | Ideal para contrastar conceptos que se parecen, clarificar debates y evitar confusiones. |
| **07** | `07_SLIDES_Guia-Visual-Estrategica` | Presentación conceptual de diapositivas en español para auto-explicación. | Pasá cada lámina e intentá explicar en voz alta el mecanismo a libro cerrado antes de ver el desarrollo. |
| **08** | `08_INFOGRAFIA_Panorama-Visual-80-20` | Infografía visual de alta densidad con el 20% de ideas que generan el 80% de impacto. | Tu mapa visual para memorizar flujos de causa y efecto de un solo vistazo. |
| **09** | `09_AUDIO_Analisis-Critico-y-Matices` | Audio en formato de crítica analítica profunda (límites, advertencias y casos de fallo). | Escuchalo para comprender las objeciones, los casos donde las reglas estándar fallan y los matices avanzados. |
| **10** | `10_AUDIO_Debate-Controversias` | Debate dialéctico confrontando las distintas escuelas de pensamiento del curso. | Para entender las distintas posturas cuando no hay consenso único. |
| **11** | `11_FLASHCARDS_Conceptos-Clave` | Tarjetas de consolidación y práctica a libro cerrado. | Dedicale 10-15 minutos para responder sin mirar la solución y afianzar distinciones operativas. |
| **12** | `12_SIMULACRO_Casos-Practicos` | Simulacro de evaluación de razonamiento causal y dilemas reales. | Tu prueba de fuego principal. Tu meta es superar el **80% de aciertos**. |
| **13** | `13_INFORME_Plan-de-Accion-y-Errores` | Hoja de ruta de aplicación práctica, catálogo de trampas y matriz de errores típicos. | Tu guía de ejecución práctica y catálogo de trampas para evitar equivocarte en la práctica real. |
| **14** | `14_VIDEO_Resumen-Audiovisual` | Video explicativo dinámico de consolidación y síntesis visual. | Miralo al cierre para integrar el aprendizaje de forma multisensorial. |

---

## 💬 Paso 3: Cómo Hablar con tu Tutor Socrático en el Chat

El chat de NotebookLM está calibrado con el rol del Tutor Socrático y Mentor Cognitivo de NotebookLM. **No le pidas que te haga resúmenes gigantes** (eso genera aprendizaje pasivo). Usalo como tutor socrático activo:

1. **Para iniciar la sesión**:
   > *"Iniciemos la sesión. Ponme a prueba con una pregunta de razonamiento conceptual base sobre el primer módulo."*
2. **Para someterte a Interrogación Inversa (la técnica más potente)**:
   > *"He intentado resolver/explicar esto así: [escribe tu explicación]. Compáralo directamente con el material del cuaderno y dime: 1) ¿Qué omití? 2) ¿En qué me equivoqué citando la fuente exacta?"*
3. **Si te sentís frustrado o bloqueado**:
   > *"Desmonta este concepto al átomo más básico con una analogía cotidiana, porque me siento bloqueado y necesito visualizar el mecanismo antes de continuar."*

---

## ⏱️ Paso 4: El Cronómetro de Estudio (¿Cuándo Parar?)

Para estudiar con la máxima concentración sin quemar tu cerebro, ejecutá en tu terminal:

```bash
nlm-tutor session "Nombre del Cuaderno" --duration 90
```

El script te guiará con pausas claras:
- **Minuto 00 al 15 (Activación)**: Resolvé el Diagnóstico Inicial (`01`), mirá el Mapa Mental (`02`) y el Briefing de Fuentes (`04`).
- **Minuto 15 al 75 (Esfuerzo Profundo)**: Hablá con el Tutor Socrático en el chat y resolvé el Simulacro de Casos Prácticos (`12`).
- **Minuto 75 al 90 (Cierre y Lagunas)**: Revisá la nota `00_CUADERNO_DE_LAGUNAS` para verificar qué conceptos se registraron automáticamente.
- **¡Parar estrictamente a los 90 minutos!**: El cerebro humano no puede mantener la máxima intensidad cognitiva por más tiempo. Tomate 20 minutos de descanso sin pantallas (podés salir a caminar o escuchar el Audio Inmersión `03`).

*(¿Tenés poco tiempo hoy? Ejecutá `nlm-tutor session "Nombre" --duration 45` para una micro-sesión rápida de 45 minutos enfocada en un solo concepto).*

---

## 🚦 Paso 5: El Semáforo de Avance (¿Cuándo Avanzar o Repasar?)

- 🟢 **VERDE (Acertaste el 80% o más en el Simulacro `12`)**: ¡Felicitaciones! Dominás los conceptos esenciales. Podés avanzar con tranquilidad al siguiente módulo o curso.
- 🟡 **AMARILLO / ROJO (Menos del 80%)**: **NO vuelvas a leer todo el curso desde el principio**. Esa es la trampa de la relectura. Hacé lo siguiente:
  1. Abrí la nota `00_CUADERNO_DE_LAGUNAS` en tu cuaderno.
  2. Mirá los 2 o 3 conceptos específicos que fallaste.
  3. Consultá en NotebookLM **únicamente** los párrafos o fuentes que hablan de esos 2 conceptos.
  4. Hacé una micro-sesión de 10 minutos con las Flashcards (`11`) para cerrar la brecha.

---

## 📅 Paso 6: Tu Calendario de Repasos Espaciados

La memoria humana olvida la mayor parte de lo aprendido en las primeras 24 horas si no se consolida. Para que el conocimiento pase a tu memoria de largo plazo, ejecutá:

```bash
nlm-tutor schedule "Nombre del Cuaderno"
```

El comando calculará tus fechas exactas de repaso basadas en la curva científica de consolidación:
- **Hito 0 (Inmediato)**: 10 min para revisar lagunas en `00_CUADERNO_DE_LAGUNAS`.
- **Hito 1 (+24 horas)**: 15 min de Flashcards (`11`) a libro cerrado.
- **Hito 2 (+72 horas)**: Re-evaluación ágil con el Diagnóstico Inicial (`01`).
- **Hito 3 (+7 días)**: Resolver el Simulacro de Casos Prácticos (`12`).
- **Hito 4 (+14 días)**: Repasar solo los puntos registrados en `00_CUADERNO_DE_LAGUNAS`.
- **Hito 5 (+30 días)**: Mirar las Slides (`07`) y explicar el tema completo en voz alta sin mirar apuntes.

---

## 🤖 Paso 7: Vigilancia y Renombrado Autónomo en Segundo Plano (Cero Pasos Manuales)

El sistema `nlm-tutor` gestiona automáticamente el renombramiento de todos los entregables. Cuando Google Cloud concluye el procesamiento de artefactos pesados (audio, video o slides), un daemon de vigilancia en segundo plano aplica de forma transparente los títulos canónicos numerados, sin que tengas que intervenir ni ejecutar comandos adicionales.

*(Si por alguna razón quisieras forzar una reconciliación manual inmediata, podés ejecutar en cualquier momento: `nlm-tutor rename "Nombre o ID"`).*

---

## 💡 Paso 8: Biblioteca de los 12 Prompts Maestros con 1 Toque

Podés disparar cualquiera de los 12 prompts maestros directamente desde la terminal con:

```bash
nlm-tutor prompt "Nombre del Cuaderno" <1-12> --send
```

1. **Prompt 1**: Resumen de Máximo Detalle (Construcción del Mapa Base).
2. **Prompt 2**: Explicación Didáctica de Primeros Principios (Enseñanza desde Cero).
3. **Prompt 3**: Testing de 10 Preguntas de Razonamiento Causal (No Memoria).
4. **Prompt 4**: Plan de Sesión de Alto Enfoque (Bloque de 90 Minutos).
5. **Prompt 5**: Kit de Consolidación Final & Hoja de Errores Típicos.
6. **Prompt 6**: Debates, Matices Críticos y Vías de Consenso.
7. **Prompt 7**: Mapa Mental como Syllabus Estructural.
8. **Prompt 8**: Deconstrucción 80/20 en Micro-habilidades Críticas.
9. **Prompt 9**: Autocorrección Temprana: Los 3 Errores Más Comunes.
10. **Prompt 10**: Anti-Bloqueo Conceptual: Analogía Inmediata de Núcleo.
11. **Prompt 11**: Dinámica de Sistemas: El Iceberg Estructural de 4 Capas.
12. **Prompt 12**: Dinámica de Sistemas: Bucles de Causalidad y Palancas de Alto Impacto.

---

## 📁 Paso 9: Monitorear Colecciones Nativas

Para ver qué colecciones tenés creadas en tu cuenta de Google NotebookLM y cuántos cuadernos contiene cada una:

```bash
nlm-tutor collections
```

*(Recordá que cuando usás `mcv-download --collection "Nombre"`, los cursos se agrupan automáticamente aquí sin pasos manuales previos).*

---

## 🌐 Paso 10: Conectar Múltiples Cursos y Autores (Consultas Cruzadas)

Si tenés varios cuadernos de diferentes autores sobre el mismo tema, podés hacerles una pregunta a todos juntos:

```bash
nlm-tutor cross "¿Qué dicen los diferentes autores sobre este tema y qué puntos de desacuerdo existen entre ellos?"
```

NotebookLM buscará en todos tus cuadernos a la vez y te entregará una respuesta consolidada citando a cada fuente.

---

¡Disfrutá el proceso de aprendizaje acelerado! Con este sistema tenés a tu disposición un sparring socrático de clase mundial disponible las 24 horas del día.
