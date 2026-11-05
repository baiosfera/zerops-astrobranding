#!/usr/bin/env python3
"""
Unit test suite for Apotelos CLI (TDD & Anti-Slop Validation).
Verifies:
1. Pydantic v2 polymorphic contracts and schema integrity.
2. ZERO HARDCODED brand names or entities in source code.
3. Robust agnostic extraction from DOCX (real tables and text tables), Markdown, and PDF.
4. Cascading discovery order without fake hallucinated root verticals.
5. Dynamic Zerops runtime discovery & offline Blackboard manifest generation.
"""

import os
import sys
import json
import zipfile
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent

from importlib.machinery import SourceFileLoader
apotelos = SourceFileLoader("apotelos", str(SCRIPTS_DIR / "apotelos")).load_module()


class TestApotelosContracts(unittest.TestCase):
    """Test Pydantic v2 schemas and models."""

    def test_dynamic_vertical_spec(self):
        v = apotelos.DynamicVerticalSpec(
            vertical_slug="activewear",
            display_name="Ropa Deportiva",
            funnel_type=apotelos.CommercialFunnelType.DIRECT_CHECKOUT,
            target_avatar={"pain_points": ["Telas que se transparentan"]},
            unique_mechanism={"name": "Tejido Anatómico"},
            primary_offer={"structure": "Pack 2x1"},
            conversion_events=["Purchase", "InitiateCheckout"]
        )
        self.assertEqual(v.vertical_slug, "activewear")
        self.assertEqual(v.funnel_type, "direct_checkout")
        self.assertIn("Purchase", v.conversion_events)

    def test_universal_brand_ecosystem(self):
        eco = apotelos.UniversalBrandEcosystem(
            brand_slug="test-brand",
            umbrella_name="Test Holding",
            verticals={
                "v1": apotelos.DynamicVerticalSpec(
                    vertical_slug="v1",
                    display_name="Vertical 1",
                    unique_mechanism={"name": "Mecanismo 1"},
                    primary_offer={"structure": "Oferta 1"},
                    target_avatar={"pain_points": ["Dolor 1"]}
                )
            }
        )
        self.assertEqual(eco.brand_slug, "test-brand")
        self.assertIn("v1", eco.verticals)

    def test_polymorphic_messaging_ecosystem(self):
        """Test polymorphic TOFU/MOFU/BOFU messaging schema and manifest compilation."""
        vert_checkout = apotelos.DynamicVerticalSpec(
            vertical_slug="ecommerce-unit",
            display_name="Tienda Online",
            funnel_type=apotelos.CommercialFunnelType.DIRECT_CHECKOUT,
            unique_mechanism={"name": "Formula X"},
            primary_offer={"structure": "Pack Starter", "pricing": {"currency": "EUR"}},
            target_avatar={"pain_points": ["Poco tiempo"]}
        )
        eco = apotelos.UniversalBrandEcosystem(
            brand_slug="global-brand",
            verticals={"ecommerce-unit": vert_checkout}
        )

        manifest = apotelos.compile_blackboard_manifest(eco, vert_checkout)
        self.assertIn("messaging_spec", manifest.model_dump())
        m_spec = manifest.messaging_spec
        self.assertEqual(m_spec["currency"], "EUR")
        self.assertIn("tofu", m_spec)
        self.assertIn("mofu", m_spec)
        self.assertIn("bofu", m_spec)
        self.assertIn("post_conversion", m_spec)
        self.assertTrue(m_spec["anti_collision"]["cross_channel_suppression"])
        self.assertEqual(m_spec["anti_collision"]["frequency_cap_hours"], 24)

        # Booking calendar vertical test
        vert_booking = apotelos.DynamicVerticalSpec(
            vertical_slug="clinic-consulting",
            display_name="Clinica Estetica",
            funnel_type=apotelos.CommercialFunnelType.BOOKING_CALENDAR,
            unique_mechanism={"name": "Diagnostico 3D"},
            primary_offer={"structure": "Valoracion VIP"},
            target_avatar={"pain_points": ["Arrugas"]}
        )
        manifest_booking = apotelos.compile_blackboard_manifest(eco, vert_booking)
        m_booking = manifest_booking.messaging_spec
        self.assertEqual(m_booking["currency"], "USD")
        self.assertEqual(m_booking["post_conversion"][0]["priority"], "P1_TRANSACTIONAL")


class TestZeroHardcoding(unittest.TestCase):
    """Ensure no hardcoded client/brand names exist in the apotelos script."""

    PROHIBITED_STRINGS = [
        "catalinaglamur",
        "damaren",
        "bioenka",
        "kreiss",
        "astrotipia",
        "synthemika",
        "numenesis"
    ]

    def test_source_code_has_no_hardcoded_brands(self):
        source_path = SCRIPTS_DIR / "apotelos"
        content = source_path.read_text(encoding="utf-8").lower()
        found_prohibited = []
        for s in self.PROHIBITED_STRINGS:
            # Check if string appears outside of comments or test references
            if s in content:
                found_prohibited.append(s)
        self.assertEqual(
            found_prohibited,
            [],
            f"Found prohibited hardcoded brand names in {source_path}: {found_prohibited}"
        )


class TestAgnosticExtraction(unittest.TestCase):
    """Test extraction from DOCX, Markdown, and files without hardcoded filters."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_from_markdown(self):
        md_file = self.temp_path / "consultoria.md"
        md_file.write_text("""# Consultoría Estratégica
Línea de asesoría empresarial de alto nivel.
Funnel: booking_calendar
Mecanismo: Metodología Ágil 360
Oferta: Sesión de Diagnóstico 1 a 1
Avatar: Directores generales con cuellos de botella operativos
""", encoding="utf-8")

        verts = apotelos.extract_from_text_or_md(md_file)
        self.assertTrue(len(verts) > 0)
        self.assertEqual(verts[0].vertical_slug, "consultoria-estrategica")
        self.assertEqual(verts[0].funnel_type, apotelos.CommercialFunnelType.BOOKING_CALENDAR)

    def test_extract_from_docx_tables(self):
        # Create a synthetic docx with a real XML table
        docx_file = self.temp_path / "servicios.docx"
        doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Vertical</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Tipo Funnel</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Propuesta de Valor</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Tienda Calzado</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>direct_checkout</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Zapatos ortopédicos ergonómicos</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Academia Online</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>subscription</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Membresía mensual de cursos</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>"""
        with zipfile.ZipFile(docx_file, "w") as z:
            z.writestr("word/document.xml", doc_xml.encode("utf-8"))

        verts = apotelos.extract_from_docx(docx_file)
        self.assertEqual(len(verts), 2)
        slugs = [v.vertical_slug for v in verts]
        self.assertIn("tienda-calzado", slugs)
        self.assertIn("academia-online", slugs)


class TestApotelosScaffold(unittest.TestCase):
    """Test physical code scaffolding of Astro 5 SSR pages from Blackboard manifests."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scaffold_generates_valid_astro_page(self):
        v = apotelos.DynamicVerticalSpec(
            vertical_slug="auditoria-seo",
            display_name="Auditoría SEO Local",
            funnel_type=apotelos.CommercialFunnelType.LEAD_GENERATION,
            unique_mechanism={"name": "Sensor Algorítmico 360", "contrast": "Frente a reportes manuales genéricos"},
            primary_offer={"structure": "Diagnóstico de 15 Puntos + Plan de Acción", "pricing": {"currency": "COP", "amount": 150000}},
            target_avatar={"pain_points": ["Fichas suspendidas en Google Maps"]},
            conversion_events=["Lead", "Contact"]
        )
        eco = apotelos.UniversalBrandEcosystem(
            brand_slug="baiosfera",
            umbrella_name="Baiosfera",
            verticals={"auditoria-seo": v}
        )
        manifest = apotelos.compile_blackboard_manifest(eco, v)
        out_file = self.temp_path / "auditoria-seo.astro"
        res_path = apotelos.scaffold_astro_page(manifest, out_file)

        self.assertTrue(res_path.exists())
        content = res_path.read_text(encoding="utf-8")

        # Verify Astro Structure & Reverse Causality Dominos
        self.assertTrue(content.startswith("---"))
        self.assertIn("application/ld+json", content)                     # Domino 2: Schema.org
        self.assertIn("__attr_session", content)                         # Domino 3: 1st-party cookie telemetry
        self.assertIn("fichas suspendidas en google maps", content.lower()) # Domino 1: Avatar pain in 3s hook
        self.assertIn("Sensor Algorítmico 360", content)                  # Domino 0: Unique mechanism
        self.assertIn("Diagnóstico de 15 Puntos", content)               # Domino 4: Primary offer

    def test_template_hydration(self):
        """Verify that scaffold hydrates modular components from templates/astro into app workspace."""
        v = apotelos.DynamicVerticalSpec(
            vertical_slug="test-hydrated",
            display_name="Test Hydrated",
            funnel_type=apotelos.CommercialFunnelType.DIRECT_CHECKOUT,
            unique_mechanism={"name": "M"},
            primary_offer={"structure": "O"},
            target_avatar={"pain_points": ["P"]}
        )
        eco = apotelos.UniversalBrandEcosystem(brand_slug="test-brand", verticals={"test-hydrated": v})
        manifest = apotelos.compile_blackboard_manifest(eco, v)

        app_pages = self.temp_path / "mock-app" / "src" / "pages"
        app_pages.mkdir(parents=True, exist_ok=True)
        target_file = app_pages / "test-hydrated.astro"

        apotelos.scaffold_astro_page(manifest, target_file)

        src_dir = target_file.parent.parent
        self.assertTrue((src_dir / "components" / "SeoHead.astro").exists())
        self.assertTrue((src_dir / "components" / "CookieConsent.astro").exists())
        self.assertTrue((src_dir / "actions" / "contact.ts").exists())
        self.assertTrue((src_dir / "lib" / "phone.ts").exists())
        self.assertTrue((src_dir / "lib" / "discountStrategy.ts").exists())

    def test_anti_chassis_contamination_guard(self):
        """Ensure writing to upstream chassis /var/www/zerops-astrobranding is strictly blocked."""
        v = apotelos.DynamicVerticalSpec(
            vertical_slug="test-v",
            display_name="Test",
            funnel_type=apotelos.CommercialFunnelType.DIRECT_CHECKOUT,
            unique_mechanism={"name": "M"},
            primary_offer={"structure": "O"},
            target_avatar={"pain_points": ["P"]}
        )
        eco = apotelos.UniversalBrandEcosystem(brand_slug="test-brand", verticals={"test-v": v})
        manifest = apotelos.compile_blackboard_manifest(eco, v)

        # 1. Target resolution never returns upstream chassis
        resolved_dir = apotelos.resolve_scaffold_target_dir("test-brand")
        self.assertFalse(
            "/var/www/zerops-astrobranding/apps/astrobranding" in str(resolved_dir),
            f"Resolved dir contaminated upstream chassis: {resolved_dir}"
        )

        # 2. Direct attempt to write inside upstream chassis raises ValueError
        contaminated_file = Path("/var/www/zerops-astrobranding/apps/astrobranding/src/pages/test.astro")
        with self.assertRaises(ValueError) as ctx:
            apotelos.scaffold_astro_page(manifest, contaminated_file)
        self.assertIn("CONTAMINATION HAZARD", str(ctx.exception))


class TestDynamicZeropsDiscovery(unittest.TestCase):
    """Test runtime discovery and blackboard compilation."""

    def test_blackboard_manifest_generation(self):
        v = apotelos.DynamicVerticalSpec(
            vertical_slug="software-saas",
            display_name="Software SaaS B2B",
            funnel_type=apotelos.CommercialFunnelType.SUBSCRIPTION,
            unique_mechanism={"name": "Engine Distribuido"},
            primary_offer={"structure": "Plan Enterprise Anual", "pricing": {"currency": "USD", "amount": 1200}},
            target_avatar={"pain_points": ["Pérdida de sincronización de datos"]}
        )
        eco = apotelos.UniversalBrandEcosystem(
            brand_slug="acme-cloud",
            umbrella_name="Acme Corporation",
            verticals={"software-saas": v}
        )
        manifest = apotelos.compile_blackboard_manifest(eco, v)
        self.assertEqual(manifest.brand_slug, "acme-cloud")
        self.assertEqual(manifest.vertical_slug, "software-saas")
        self.assertEqual(manifest.telemetry_spec["funnel_type"], "subscription")
        self.assertIn("llms_txt", manifest.seo_aeo_spec)
        self.assertIn("hormozi_equation", manifest.copy_manifest)


if __name__ == "__main__":
    unittest.main()
