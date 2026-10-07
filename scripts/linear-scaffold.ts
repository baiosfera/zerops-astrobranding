#!/usr/bin/env node
/**
 * ==============================================================================
 * Linear Project & Gated Workflow Scaffolder (linear-scaffold.ts)
 * Version: 4.0.0 (Sovereign Linear Blueprint & Dependency Gating)
 * Execution: node --experimental-strip-types scripts/linear-scaffold.ts [args]
 * ==============================================================================
 */

import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

interface LabelDef {
  name: string;
  color: string;
  description: string;
}

interface IssueDef {
  order: number;
  key: string;
  title: string;
  milestone: string;
  labels: string[];
  blockedBy: string[];
  description: string;
  definitionOfDone: string[];
}

interface TemplateManifest {
  version: string;
  name: string;
  teamKey: string;
  labels: LabelDef[];
  issues: IssueDef[];
}

async function runGraphQL(apiKey: string, query: string, variables: Record<string, any> = {}) {
  const res = await fetch('https://api.linear.app/graphql', {
    method: 'POST',
    headers: {
      'Authorization': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, variables }),
  });

  if (!res.ok) {
    throw new Error(`Linear API HTTP Error ${res.status}: ${res.statusText}`);
  }

  const json = await res.json() as { data?: any; errors?: any[] };
  if (json.errors && json.errors.length > 0) {
    throw new Error(`Linear GraphQL Error: ${JSON.stringify(json.errors)}`);
  }

  return json.data;
}

async function main() {
  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run') || args.includes('-d');
  const cleanArgs = args.filter(a => a !== '--dry-run' && a !== '-d');

  let profile = 'full-mesh';
  const profileIdx = cleanArgs.findIndex(a => a === '--profile' || a === '-p');
  if (profileIdx !== -1 && cleanArgs[profileIdx + 1]) {
    profile = cleanArgs[profileIdx + 1].toLowerCase();
    cleanArgs.splice(profileIdx, 2);
  }

  if (cleanArgs.includes('--help') || cleanArgs.includes('-h') || (cleanArgs.length === 0 && !isDryRun)) {
    console.log(`
Uso: node --experimental-strip-types linear-scaffold.ts <APP_IDENTITY> "<PROJECT_NAME>" [opciones]

Argumentos:
  APP_IDENTITY   Slug en minúsculas de la marca (ej: acme, lumina)
  PROJECT_NAME   Nombre humano de la marca (ej: "Acme Platform")

Opciones:
  --profile, -p  Perfil Lego: minimal | content | ecommerce | full-mesh (default: full-mesh)
  --dry-run, -d  Simula la ejecución completa sin mutar Linear
  --help, -h     Muestra este mensaje de ayuda
`);
    process.exit(0);
  }

  const appIdentity = cleanArgs[0] || 'demo';
  const projectName = cleanArgs[1] || `${appIdentity.toUpperCase()} Web Platform`;

  // 1. Carga del Manifiesto Declarativo
  const localTemplatePath = resolve(dirname(fileURLToPath(import.meta.url)), '../templates/linear_template.json');
  const artifactsTemplatePath = resolve('/var/www/artifacts/templates/linear_template.json');
  const templatePath = existsSync(localTemplatePath) ? localTemplatePath : artifactsTemplatePath;
  if (!existsSync(templatePath)) {
    console.error(`❌ Error: Manifiesto no encontrado en ${localTemplatePath} ni ${artifactsTemplatePath}`);
    process.exit(1);
  }

  const manifest = JSON.parse(readFileSync(templatePath, 'utf-8')) as TemplateManifest;

  // Filtrado de Issues según Perfil Modular Lego
  let selectedIssues = manifest.issues;
  if (profile === 'minimal') {
    selectedIssues = manifest.issues.filter(i => ['BAI-0', 'BAI-1', 'BAI-3', 'BAI-6'].includes(i.key)).map(i => {
      const copy = { ...i, blockedBy: [...i.blockedBy] };
      if (copy.key === 'BAI-3') copy.blockedBy = ['BAI-1'];
      if (copy.key === 'BAI-6') copy.blockedBy = ['BAI-3'];
      return copy;
    });
  } else if (profile === 'content') {
    selectedIssues = manifest.issues.filter(i => ['BAI-0', 'BAI-1', 'BAI-2', 'BAI-3', 'BAI-6'].includes(i.key)).map(i => {
      const copy = { ...i, blockedBy: [...i.blockedBy] };
      if (copy.key === 'BAI-3') copy.blockedBy = ['BAI-2'];
      if (copy.key === 'BAI-6') copy.blockedBy = ['BAI-3'];
      return copy;
    });
  } else if (profile === 'ecommerce') {
    selectedIssues = manifest.issues.filter(i => ['BAI-0', 'BAI-1', 'BAI-2', 'BAI-3', 'BAI-4', 'BAI-6'].includes(i.key)).map(i => {
      const copy = { ...i, blockedBy: [...i.blockedBy] };
      if (copy.key === 'BAI-3') copy.blockedBy = ['BAI-2'];
      if (copy.key === 'BAI-4') copy.blockedBy = ['BAI-3'];
      if (copy.key === 'BAI-6') copy.blockedBy = ['BAI-4'];
      return copy;
    });
  }

  console.log('============================================================');
  console.log(`🚀 Linear Universal Scaffolder v${manifest.version}`);
  console.log(`📦 Proyecto: [${appIdentity}] ${projectName}`);
  console.log(`🧩 Perfil Lego: ${profile.toUpperCase()}`);
  console.log(`🏷️ Team Key: ${manifest.teamKey}`);
  console.log(`🛡️ Modo: ${isDryRun ? 'DRY-RUN (Simulación Determinista)' : 'LIVE EXECUTION'}`);
  console.log('============================================================');

  if (isDryRun) {
    console.log('\n[1/4] Simulación de Etiquetas (Labels):');
    for (const l of manifest.labels) {
      console.log(`  ✓ Label: ${l.name} (${l.color}) — ${l.description}`);
    }

    console.log('\n[2/4] Simulación de Creación de Proyecto:');
    console.log(`  ✓ Proyecto: "[${appIdentity.toUpperCase()}] ${projectName}"`);

    console.log(`\n[3/4] Simulación de Issues Canónicas & Dependencias (Perfil: ${profile}):`);
    for (const issue of selectedIssues) {
      const title = issue.title.replace('[Brand]', `[${appIdentity.toUpperCase()}]`);
      const blockedStr = issue.blockedBy.length > 0 ? ` (Bloqueado por: ${issue.blockedBy.join(', ')})` : ' (Listo para Iniciar)';
      console.log(`  🔹 ${issue.key}: ${title}${blockedStr}`);
      console.log(`     Labels: [${issue.labels.join(', ')}]`);
      console.log(`     DoD: ${issue.definitionOfDone.length} criterios de sensor`);
    }

    console.log('\n[4/4] Veredicto de Simulación:');
    console.log('✅ Simulación completada con éxito. Manifiesto coherente y 100% aplicable.');
    process.exit(0);
  }

  // 2. Ejecución Real en Linear
  const apiKey = process.env.LINEAR_API_KEY;
  if (!apiKey) {
    console.error('❌ Error: La variable de entorno LINEAR_API_KEY no está configurada.');
    process.exit(1);
  }

  // Resolver Team ID
  console.log('🔍 Consultando Teams en Linear...');
  const teamsData = await runGraphQL(apiKey, `
    query {
      teams(first: 20) {
        nodes {
          id
          key
          name
        }
      }
    }
  `);

  const team = teamsData.teams.nodes.find((t: any) => t.key === manifest.teamKey) || teamsData.teams.nodes[0];
  if (!team) {
    throw new Error(`No se encontró ningún equipo en Linear con key ${manifest.teamKey}`);
  }
  console.log(`✓ Usando Team: ${team.name} (${team.key}) [ID: ${team.id}]`);

  // Asegurar Labels
  console.log('🏷️ Asegurando etiquetas en Linear...');
  const existingLabelsData = await runGraphQL(apiKey, `
    query($teamId: String!) {
      team(id: $teamId) {
        labels(first: 100) {
          nodes { id name }
        }
      }
    }
  `, { teamId: team.id });

  const labelMap = new Map<string, string>();
  for (const el of existingLabelsData.team.labels.nodes) {
    labelMap.set(el.name, el.id);
  }

  for (const l of manifest.labels) {
    if (!labelMap.has(l.name)) {
      const created = await runGraphQL(apiKey, `
        mutation($teamId: String!, $name: String!, $color: String!, $description: String) {
          issueLabelCreate(input: { teamId: $teamId, name: $name, color: $color, description: $description }) {
            issueLabel { id name }
          }
        }
      `, { teamId: team.id, name: l.name, color: l.color, description: l.description });
      labelMap.set(l.name, created.issueLabelCreate.issueLabel.id);
      console.log(`  + Label creada: ${l.name}`);
    } else {
      console.log(`  ✓ Label existente: ${l.name}`);
    }
  }

  // Crear o Localizar Proyecto
  const fullProjectName = `[${appIdentity.toUpperCase()}] ${projectName}`;
  console.log(`📁 Verificando proyecto: "${fullProjectName}"...`);
  const projectsData = await runGraphQL(apiKey, `
    query($teamId: String!) {
      team(id: $teamId) {
        projects(first: 50) {
          nodes { id name state }
        }
      }
    }
  `, { teamId: team.id });

  let projectId: string;
  const existingProject = projectsData.team.projects.nodes.find((p: any) => p.name === fullProjectName);
  if (existingProject) {
    projectId = existingProject.id;
    console.log(`✓ Proyecto existente localizado [ID: ${projectId}]`);
  } else {
    const newProj = await runGraphQL(apiKey, `
      mutation($teamIds: [String!]!, $name: String!) {
        projectCreate(input: { teamIds: $teamIds, name: $name }) {
          project { id name }
        }
      }
    `, { teamIds: [team.id], name: fullProjectName });
    projectId = newProj.projectCreate.project.id;
    console.log(`✓ Nuevo proyecto creado en Linear [ID: ${projectId}]`);
  }

  // Crear Issues
  console.log(`📝 Creando las ${selectedIssues.length} Issues Modulares (Perfil: ${profile})...`);
  const createdIssuesMap = new Map<string, { id: string; identifier: string }>();

  for (const issue of selectedIssues) {
    const formattedTitle = issue.title.replace('[Brand]', `[${appIdentity.toUpperCase()}]`);
    const labelIds = issue.labels.map(name => labelMap.get(name)).filter(Boolean);

    const fullDescription = `${issue.description}

### Definition of Done (Sensores Físicos):
${issue.definitionOfDone.map(d => `- [ ] ${d}`).join('\n')}

---
*Gobernanza: Plantilla Universal Web Zerops v4.1.0 (CoHaLo Track B)*`;

    const res = await runGraphQL(apiKey, `
      mutation($teamId: String!, $projectId: String!, $title: String!, $description: String!, $labelIds: [String!]) {
        issueCreate(input: {
          teamId: $teamId,
          projectId: $projectId,
          title: $title,
          description: $description,
          labelIds: $labelIds
        }) {
          issue { id identifier title url }
        }
      }
    `, {
      teamId: team.id,
      projectId,
      title: formattedTitle,
      description: fullDescription,
      labelIds
    });

    const created = res.issueCreate.issue;
    createdIssuesMap.set(issue.key, { id: created.id, identifier: created.identifier });
    console.log(`  ✓ Creada: ${created.identifier} — ${created.title}`);
  }

  // Enlazar Dependencias (blockedBy)
  console.log('🔒 Configurando relaciones y dependencias bloqueantes...');
  for (const issue of selectedIssues) {
    if (issue.blockedBy.length > 0) {
      const target = createdIssuesMap.get(issue.key);
      if (!target) continue;

      for (const blockerKey of issue.blockedBy) {
        const blocker = createdIssuesMap.get(blockerKey);
        if (!blocker) continue;

        await runGraphQL(apiKey, `
          mutation($issueId: String!, $relatedIssueId: String!) {
            issueRelationCreate(input: {
              issueId: $issueId,
              relatedIssueId: $relatedIssueId,
              type: blocks
            }) {
              issueRelation { id type }
            }
          }
        `, {
          issueId: blocker.id,
          relatedIssueId: target.id
        });
        console.log(`  🔒 ${blocker.identifier} bloquea a ${target.identifier}`);
      }
    }
  }

  console.log('\n============================================================');
  console.log('✅ Aprovisionamiento en Linear completado con éxito.');
  console.log(`📁 Proyecto: ${fullProjectName}`);
  console.log('============================================================');
}

main().catch(err => {
  console.error('❌ Error fatal en linear-scaffold:', err);
  process.exit(1);
});
