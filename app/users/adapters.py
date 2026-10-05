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
        try:
            return super().send_mail(template_prefix, email, context)
        except Exception as e:
            audit_logger.error(f"EMAIL SEND FAILED: Template {template_prefix} to {email}. Error: {e}")
            raise

    def get_logout_redirect_url(self, request):
        from django.urls import reverse
        return reverse('core:home')

    def add_message(
        self,
        request,
        level,
        message_template=None,
        message_context=None,
        extra_tags="",
        message=None,
    ):
        if message_template == "account/messages/logged_out.txt":
            return
        super().add_message(
            request,
            level,
            message_template=message_template,
            message_context=message_context,
            extra_tags=extra_tags,
            message=message,
        )


