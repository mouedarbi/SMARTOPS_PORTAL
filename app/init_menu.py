from core.models import Menu, MenuItem
from wagtail.models import Locale

def run():
    fr_locale = Locale.objects.get(language_code='fr')
    menu, created = Menu.objects.get_or_create(
        slug='main-menu', 
        locale=fr_locale, 
        defaults={'title': 'Menu Principal'}
    )
    
    if created:
        MenuItem.objects.create(page=menu, link_title='Accueil', link_url='/')
        MenuItem.objects.create(page=menu, link_title='Modules', link_url='/fr/catalog/')
        MenuItem.objects.create(page=menu, link_title='Blog & FAQ', link_url='/fr/content/')
        print("Menu 'main-menu' créé avec succès en Français.")
    else:
        print("Le menu 'main-menu' existe déjà.")

if __name__ == "__main__":
    run()
