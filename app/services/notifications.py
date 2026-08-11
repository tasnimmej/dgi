import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION EMAIL (À modifier avec vos vrais identifiants) ---
# Pour tester, vous pouvez utiliser un compte Gmail ou un service comme Mailtrap.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_EXPEDITEUR = "votre.email@gmail.com"
MOT_DE_PASSE_EMAIL = "votre_mot_de_passe_application"  # Gmail nécessite un mot de passe d'application

def envoyer_email_alerte(destinataire: str, sujet: str, contenu: str):
    """
    Envoie un email à l'utilisateur.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_EXPEDITEUR
        msg['To'] = destinataire
        msg['Subject'] = sujet

        msg.attach(MIMEText(contenu, 'plain'))

        # Connexion au serveur SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_EMAIL)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email envoyé à {destinataire}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")
        return False