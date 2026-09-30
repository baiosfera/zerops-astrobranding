import type { APIRoute } from "astro";

export const GET: APIRoute = async () => {
  const content = `# AstroBranding
> Plataforma Soberana de Posicionamiento Arquetípico y Branding Integral en Zerops.

## Recursos Principales
- [/docs](/docs): Documentación técnica del ecosistema y microservicios
- [/fase0](/fase0): Diagnóstico arquetípico e ingreso asistido
- [/checkout](/checkout): Pasarelas de pago y embudo de conversión

## Opcional
- [/desk/studio](/desk/studio): Preview interactivo de diseño y tokens
`;

  return new Response(content, {
    status: 200,
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    },
  });
};
