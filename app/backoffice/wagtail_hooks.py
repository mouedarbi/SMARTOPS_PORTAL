from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

@hooks.register('register_admin_menu_item')
def register_django_admin_menu_item():
    return MenuItem(
        'Django Admin', 
        '/django-admin/', 
        icon_name='cog', 
        order=10000
    )

@hooks.register('register_admin_menu_item')
def register_backoffice_menu_item():
    return MenuItem(
        'Backoffice Market', 
        reverse('backoffice:index'), 
        icon_name='home', 
        order=10001
    )
