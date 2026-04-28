# app/users/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_client_ip(self, request):
        # Récupération sécurisée de l'IP derrière Nginx
        ip = request.META.get('HTTP_X_REAL_IP') or \
             request.META.get('HTTP_X_FORWARDED_FOR') or \
             request.META.get('REMOTE_ADDR')

        if not ip:
            return '127.0.0.1' # Évite le crash 403 si l'IP est indéterminée

        return ip.split(',')[0].strip()
