# app/users/adapters.py
import logging

from allauth.account.adapter import DefaultAccountAdapter

audit_logger = logging.getLogger('audit')

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_client_ip(self, request):
        # Récupération sécurisée de l'IP derrière Nginx
        ip = request.META.get('HTTP_X_REAL_IP') or \
             request.META.get('HTTP_X_FORWARDED_FOR') or \
             request.META.get('REMOTE_ADDR')

        if not ip:
            return '127.0.0.1' # Évite le crash 403 si l'IP est indéterminée

        return ip.split(',')[0].strip()

    def send_password_reset_mail(self, user, email, context):
        audit_logger.info(
            f"PASSWORD RESET REQUESTED: Reset link sent to {email} for user {user.username} (ID: {user.pk})."
        )
        return super().send_password_reset_mail(user, email, context)

    def send_mail(self, template_prefix, email, context):
        if template_prefix == 'account/email/unknown_account':
            audit_logger.warning(f"PASSWORD RESET REQUEST FAILED: No active account for email {email}.")
        try:
            return super().send_mail(template_prefix, email, context)
        except Exception as e:
            audit_logger.error(f"EMAIL SEND FAILED: Template {template_prefix} to {email}. Error: {e}")
            raise

