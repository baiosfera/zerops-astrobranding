import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate, make_msgid

def build_and_send_invitation(to_email: str = "juandameren@gmail.com", recipient_name: str = "Juan"):
    # 1. Credentials & Configuration
    smtp_host = "email-smtp.us-east-1.amazonaws.com"
    smtp_port = 587
    smtp_user = os.environ.get("SES_SMTP_USER")
    smtp_pass = os.environ.get("SES_SMTP_PASSWORD")
    from_email = os.environ.get("AWS_FROM_EMAIL", "web@elplacerdecompartir.com")
    from_name = "El Placer de Compartir"

    if not smtp_user or not smtp_pass:
        raise ValueError("Missing SES_SMTP_USER or SES_SMTP_PASSWORD environment variables")

    subject = "🔥 Invitación Especial: Evento Aliado Impacto Producciones (Sábado 10 de Octubre) • Centro Cultural"

    # Paths to media assets
    flyer_path = "/var/www/webprod/public/media/eventos-aliados/sabado-10-octubre_impacto-producciones.jpg"
    logo_path = "/var/www/webprod/public/media/logo_elplacerdc_x.jpg"

    # 2. Construct Message Container
    # Root: multipart/related (allows inline images with CID)
    msg_root = MIMEMultipart("related")
    msg_root["Subject"] = subject
    msg_root["From"] = f"{from_name} <{from_email}>"
    msg_root["To"] = f"{recipient_name} <{to_email}>"
    msg_root["Date"] = formatdate(localtime=True)
    msg_root["Message-ID"] = make_msgid(domain="elplacerdecompartir.com")
    
    # Deliverability Headers (RFC 8058 & Anti-Spam Standards)
    unsub_mailto = f"mailto:{from_email}?subject=Baja%20Comunidad%20ElPlacerDC&body=Solicito%20remover%20{to_email}%20de%20la%20lista"
    msg_root["List-Unsubscribe"] = f"<{unsub_mailto}>"
    msg_root["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg_root["X-Entity-Ref-ID"] = f"EPDC-EVENT-ALIADO-{int(os.times()[4])}"

    # Container for alternative representations (plain + html)
    msg_alt = MIMEMultipart("alternative")
    msg_root.attach(msg_alt)

    # 3. Plain Text Version (Essential for spam filters & accessibility)
    plain_text = f"""🔥 INVITACIÓN ESPECIAL: EVENTO ALIADO IMPACTO PRODUCCIONES
Centro Cultural El Placer de Compartir • Bogotá (+21)

Hola {recipient_name} ✨

Nuestros aliados de Impacto Producciones se toman la casa este Sábado 10 de Octubre para una noche inolvidable en nuestro escenario central: música, shows, performances en vivo y atmósfera de alta energía.

FICHA TÉCNICA DE LA VELADA:
• Fecha: Sábado, 10 de Octubre
• Horario Entrada Libre: Sin cover de 7:00 PM a 9:30 PM (Con reserva previa)
• Show Central: Fire Show Especial 🔥 En vivo
• Instalaciones: 3 Ambientes, Escenario Central y Habitaciones Privadas
• Ubicación: Calle 67 # 23-46 Piso 2, Bogotá (Parqueadero cercano)

SOBRE NUESTRO CENTRO CULTURAL:
Concebido sin zonas húmedas comerciales, es un espacio multidisciplinario para la libertad relacional y el consentimiento lúcido sobre el consumo inmediato.

RESERVA TU PASE OFICIAL CON CÓDIGO QR:
Genera tu entrada sin cover directamente aquí:
👉 https://elplacerdecompartir.com/eventos/impacto-10-oct

PROGRAMA DE EMBAJADORES:
¿Vienes con tu grupo o pareja? Comparte tu enlace exclusivo de embajador. Por cada 3 reservas generadas, recibes 1 entrada 100% gratuita:
👉 https://elplacerdecompartir.com/dashboard

Atención oficial WhatsApp: +57 319 419 4785
Canal Oficial en X: @ElPlacerDC

Para darte de baja de futuras convocatorias:
{unsub_mailto}
"""
    msg_alt.attach(MIMEText(plain_text, "plain", "utf-8"))

    # 4. Rich HTML Version (Brandbook Tokens, Inline CSS, <85 KB)
    html_content = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="es" xml:lang="es" translate="no" class="notranslate">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="google" content="notranslate" />
  <meta name="format-detection" content="telephone=no" />
  <title>{subject}</title>
  <style type="text/css">
    @media only screen and (max-width: 600px) {{
      .wrapper-table {{ width: 100% !important; }}
      .content-padding {{ padding: 22px 18px !important; }}
      .header-padding {{ padding: 28px 18px 16px 18px !important; }}
      .hero-img {{ width: 100% !important; height: auto !important; }}
      .grid-box {{ display: block !important; width: 100% !important; margin-bottom: 10px !important; }}
      .btn-cta {{ display: block !important; width: 100% !important; box-sizing: border-box !important; text-align: center !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #0d0612; color: #F7F4EE; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
  
  <!-- Preheader text hidden in inbox view -->
  <div style="display: none; font-size: 1px; color: #0d0612; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
    Nuestros aliados de Impacto Producciones se toman la casa este Sábado 10 de Octubre en Bogotá. Sin cover de 7:00 a 9:30 PM con reserva previa.
  </div>

  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0d0612; margin: 0; padding: 0;">
    <tr>
      <td align="center" style="padding: 24px 12px 40px 12px;">
        
        <table role="presentation" class="wrapper-table" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #180A22; border: 1px solid #3d1b54; border-radius: 8px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
          
          <!-- Top Accent Gradient Line -->
          <tr>
            <td height="5" style="background: linear-gradient(90deg, #8E4A8C 0%, #C5A059 50%, #B84A39 100%); line-height: 5px; font-size: 5px;">&nbsp;</td>
          </tr>

          <!-- Header with Brand Logo -->
          <tr>
            <td align="center" class="header-padding" style="padding: 34px 30px 18px 30px; text-align: center;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 12px auto;">
                <tr>
                  <td align="center">
                    <img src="cid:logo_elplacerdc" alt="El Placer de Compartir" width="76" height="76" style="width: 76px; height: 76px; border-radius: 50%; border: 2px solid #C5A059; display: block; object-fit: cover;" />
                  </td>
                </tr>
              </table>

              <div style="color: #C5A059; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 6px; font-weight: bold;">
                Centro Cultural &bull; Bogotá
              </div>
              <div style="color: #F7F4EE; font-size: 22px; letter-spacing: 2px; font-weight: 700; line-height: 1.3; font-family: 'Cinzel', Georgia, serif; text-transform: uppercase;">
                El Placer de Compartir
              </div>
              <div style="margin-top: 10px; width: 44px; height: 2px; background-color: #C5A059; line-height: 2px; font-size: 2px;">&nbsp;</div>
            </td>
          </tr>

          <!-- Main Content Body -->
          <tr>
            <td class="content-padding" style="padding: 16px 32px 28px 32px; font-size: 15px; line-height: 1.7; color: #D6D0D8;">
              
              <!-- Badge Evento Aliado -->
              <div style="text-align: center; margin-bottom: 18px;">
                <span style="display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; background-color: rgba(142, 74, 140, 0.25); color: #f3e5f5; border: 1px solid rgba(142, 74, 140, 0.5);">
                  🔥 Evento Aliado en Nuestra Sede
                </span>
              </div>

              <!-- Main Event Headline -->
              <h1 style="margin: 0 0 14px 0; color: #F7F4EE; font-size: 23px; font-weight: 700; font-family: 'Cinzel', Georgia, serif; text-align: center; line-height: 1.3;">
                Impacto Producciones — Sábado 10
              </h1>

              <p style="margin: 0 0 18px 0; font-size: 16px; color: #F7F4EE;">
                Hola <strong style="color: #EAD397;">{recipient_name}</strong> ✨
              </p>

              <p style="margin: 0 0 18px 0; line-height: 1.6; color: #D6D0D8;">
                Nuestros aliados de <strong>Impacto Producciones</strong> se toman la casa. Te invitamos a una noche distinta con música, shows, performances en vivo y atmósfera de alta energía en nuestro escenario central en Bogotá.
              </p>

              <!-- Flyer Image Container -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 22px 0 26px 0;">
                <tr>
                  <td align="center" style="padding: 0;">
                    <a href="https://elplacerdecompartir.com/eventos/impacto-10-oct" target="_blank" style="text-decoration: none;">
                      <img class="hero-img" src="cid:flyer_impacto" alt="Flyer Impacto Producciones Sábado 10 de Octubre" width="536" style="width: 100%; max-width: 536px; height: auto; display: block; border-radius: 8px; border: 1px solid rgba(142, 74, 140, 0.4); box-shadow: 0 8px 24px rgba(0,0,0,0.4);" />
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Highlights Grid (2x2) -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 10px 0 24px 0;">
                <tr>
                  <td class="grid-box" width="48%" valign="top" style="padding: 12px; background-color: #120718; border: 1px solid rgba(142, 74, 140, 0.35); border-radius: 6px;">
                    <div style="font-size: 10px; color: rgba(243, 229, 245, 0.6); text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Entrada Libre</div>
                    <div style="color: #F7F4EE; font-size: 13px; font-weight: 600; margin-top: 3px;">Sin cover 7:00 a 9:30 PM</div>
                    <div style="font-size: 11px; color: #81c784; margin-top: 2px;">✓ Con reserva previa</div>
                  </td>
                  <td width="4%">&nbsp;</td>
                  <td class="grid-box" width="48%" valign="top" style="padding: 12px; background-color: #120718; border: 1px solid rgba(142, 74, 140, 0.35); border-radius: 6px;">
                    <div style="font-size: 10px; color: rgba(243, 229, 245, 0.6); text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Show Central</div>
                    <div style="color: #F7F4EE; font-size: 13px; font-weight: 600; margin-top: 3px;">Fire Show Especial 🔥</div>
                    <div style="font-size: 11px; color: #EAD397; margin-top: 2px;">Performance en vivo</div>
                  </td>
                </tr>
                <tr><td height="10" colspan="3" style="line-height: 10px; font-size: 10px;">&nbsp;</td></tr>
                <tr>
                  <td class="grid-box" width="48%" valign="top" style="padding: 12px; background-color: #120718; border: 1px solid rgba(142, 74, 140, 0.35); border-radius: 6px;">
                    <div style="font-size: 10px; color: rgba(243, 229, 245, 0.6); text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Instalaciones</div>
                    <div style="color: #F7F4EE; font-size: 13px; font-weight: 600; margin-top: 3px;">3 Ambientes</div>
                    <div style="font-size: 11px; color: rgba(243, 229, 245, 0.7); margin-top: 2px;">Habitaciones privadas</div>
                  </td>
                  <td width="4%">&nbsp;</td>
                  <td class="grid-box" width="48%" valign="top" style="padding: 12px; background-color: #120718; border: 1px solid rgba(142, 74, 140, 0.35); border-radius: 6px;">
                    <div style="font-size: 10px; color: rgba(243, 229, 245, 0.6); text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Ubicación</div>
                    <div style="color: #F7F4EE; font-size: 13px; font-weight: 600; margin-top: 3px;">Calle 67 # 23-46 Piso 2</div>
                    <div style="font-size: 11px; color: rgba(243, 229, 245, 0.7); margin-top: 2px;">Bogotá &bull; Parqueadero cerca</div>
                  </td>
                </tr>
              </table>

              <!-- Community Philosophy Callout -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 20px 0; background-color: #100615; border-left: 3px solid #C5A059; border-radius: 4px;">
                <tr>
                  <td style="padding: 14px 16px; font-size: 13px; line-height: 1.6; color: #D6D0D8;">
                    🏛️ <strong>Espacio Seguro & Consciente:</strong> En nuestro Centro Cultural prima el consentimiento lúcido y el respeto mutuo. Un ambiente multidisciplinario concebido sin presiones comerciales. No somos un bar swinger tradicional ni contamos con zonas húmedas.
                  </td>
                </tr>
              </table>

              <!-- Call to Action Button: Reserve QR Pass -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 28px 0 20px 0;">
                <tr>
                  <td align="center">
                    <a href="https://elplacerdecompartir.com/eventos/impacto-10-oct" target="_blank" class="btn-cta" style="background-color: #8E4A8C; border: 1px solid #a35da1; border-radius: 6px; color: #ffffff !important; display: inline-block; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: bold; letter-spacing: 1.5px; text-decoration: none; padding: 16px 36px; text-transform: uppercase; box-shadow: 0 4px 14px rgba(142, 74, 140, 0.4);">
                      <!--[if mso]>&nbsp;&nbsp;<![endif]-->
                      RESERVAR PASE CON CÓDIGO QR →
                      <!--[if mso]>&nbsp;&nbsp;<![endif]-->
                    </a>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top: 10px;">
                    <span style="font-size: 11px; color: #EAD397;">* Válido para ingreso sin cover de 7:00 a 9:30 PM con tu QR en pantalla</span>
                  </td>
                </tr>
              </table>

              <!-- Ambassador Referral Section -->
              <div style="background-color: #120718; border: 1px dashed rgba(197, 160, 89, 0.5); border-radius: 6px; padding: 16px 20px; margin: 26px 0 10px 0; text-align: center;">
                <div style="color: #C5A059; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;">
                  Programa Oficial de Embajadores
                </div>
                <div style="color: #F7F4EE; font-size: 13px; font-weight: 600; margin-bottom: 6px;">
                  ¿Vienes en grupo o con amigos? Gana Entradas Gratuitas
                </div>
                <p style="font-size: 12px; color: rgba(247, 244, 238, 0.75); line-height: 1.5; margin: 0 0 10px 0;">
                  Comparte tu enlace exclusivo de embajador: por cada 3 compras o reservas generadas con tu link, ¡el sistema te acredita automáticamente 1 pase gratuito!
                </p>
                <a href="https://elplacerdecompartir.com/dashboard" target="_blank" style="color: #EAD397; font-size: 11px; font-weight: bold; text-decoration: underline; text-transform: uppercase; letter-spacing: 1px;">
                  Acceder a mi Panel de Embajador →
                </a>
              </div>

            </td>
          </tr>

          <!-- Footer with RFC 8058 & Institutional Notice -->
          <tr>
            <td style="padding: 24px 30px; background-color: #0b0310; border-top: 1px solid #230c31; text-align: center;">
              <p style="margin: 0 0 6px 0; color: #C5A059; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; font-weight: bold;">
                El Placer de Compartir &bull; Centro Cultural
              </p>
              <p style="margin: 0 0 10px 0; color: #7B727F; font-size: 11px; line-height: 1.5;">
                Bogotá, Colombia &bull; Calle 67 # 23-46 Piso 2<br/>
                Línea Oficial WhatsApp: +57 319 419 4785 &bull; Canal Oficial en X: <a href="https://x.com/ElPlacerDC" target="_blank" style="color: #C5A059; text-decoration: none;">@ElPlacerDC</a><br/>
                Comunidad Mente Abierta &bull; Exclusivo para mayores de 21 años.
              </p>
              <p style="margin: 0; color: #554d58; font-size: 10px; line-height: 1.6;">
                Recibes esta invitación como contacto selecto de nuestra red cultural.<br/>
                Para darte de baja de futuras convocatorias de eventos: <a href="{unsub_mailto}" style="color: #8E4A8C; text-decoration: underline;">Darme de baja inmediata (1-Click)</a>
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""
    msg_alt.attach(MIMEText(html_content, "html", "utf-8"))

    # 5. Attach Media as Inline CID Images
    # Flyer Image
    if os.path.exists(flyer_path):
        with open(flyer_path, "rb") as f:
            img_flyer = MIMEImage(f.read(), _subtype="jpeg")
            img_flyer.add_header("Content-ID", "<flyer_impacto>")
            img_flyer.add_header("Content-Disposition", "inline", filename="sabado-10-octubre_impacto-producciones.jpg")
            msg_root.attach(img_flyer)
        print("✓ Flyer adjuntado con Content-ID: <flyer_impacto>")
    else:
        print(f"⚠️ Flyer no encontrado en {flyer_path}")

    # Logo Image
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            img_logo = MIMEImage(f.read(), _subtype="jpeg")
            img_logo.add_header("Content-ID", "<logo_elplacerdc>")
            img_logo.add_header("Content-Disposition", "inline", filename="logo_elplacerdc_x.jpg")
            msg_root.attach(img_logo)
        print("✓ Logo adjuntado con Content-ID: <logo_elplacerdc>")
    else:
        print(f"⚠️ Logo no encontrado en {logo_path}")

    # 6. Dispatch via AWS SES SMTP
    print(f"\nConectando a {smtp_host}:{smtp_port} vía TLS...")
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        print("✓ Autenticación SMTP SES exitosa.")
        print(f"Enviando correo desde <{from_email}> a <{to_email}>...")
        server.sendmail(from_email, [to_email], msg_root.as_string())

    print(f"\n🎉 ¡Correo enviado con éxito a {to_email}!")
    return True

if __name__ == "__main__":
    import sys
    recipient = sys.argv[1] if len(sys.argv) > 1 else "juandameren@gmail.com"
    name = sys.argv[2] if len(sys.argv) > 2 else "Juan"
    build_and_send_invitation(recipient, name)
