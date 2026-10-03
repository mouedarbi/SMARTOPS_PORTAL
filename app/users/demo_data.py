"""
Fichier : demo_data.py
Projet : Marketplace SMARTOPS
Application : users
Auteur : Mohamed Ouedarbi
Version : 1.0
Description : Identités des clients fictifs de démonstration.
              Adresses en « plus addressing » Gmail : tous les e-mails des comptes de
              démonstration arrivent dans la boîte du projet, aucun n'est envoyé à un tiers.
              70 % de comptes professionnels (PME, indépendants, sociétés de maintenance
              établies en Belgique), 30 % de particuliers. Entreprises, adresses et numéros de
              TVA sont fictifs (numéros au format belge valide, clé modulo 97).
"""

DEMO_MAILBOX = ('opensmartops', 'gmail.com')
PROFESSIONAL_SHARE = 7  # sur 10

LEGAL_FORMS = ['SRL', 'SA', 'SC', 'BV', 'NV']
ACTIVITIES = ['Maintenance', 'Maintenance Industrielle', 'Techniek', 'Facility Services', 'Engineering',
              'Électromécanique', 'HVAC Services', 'Industrie']
STREETS = ['Rue de la Station', "Chaussée d'Anvers", 'Avenue Louise', 'Rue du Parc', 'Kerkstraat',
           'Stationsstraat', 'Rue de l\'Industrie', 'Zoning Industriel', 'Rue des Artisans', 'Molenstraat']
CITIES = [('1000', 'Bruxelles'), ('4000', 'Liège'), ('5000', 'Namur'), ('6000', 'Charleroi'),
          ('7000', 'Mons'), ('1300', 'Wavre'), ('2000', 'Antwerpen'), ('9000', 'Gent'),
          ('3000', 'Leuven'), ('8000', 'Brugge'), ('1400', 'Nivelles'), ('6700', 'Arlon')]


def demo_email(number):
    """Adresse de démonstration n° `number` : opensmartops+user<number>@gmail.com."""
    local, domain = DEMO_MAILBOX
    return f"{local}+user{number}@{domain}"


def is_professional_slot(index):
    """7 comptes sur 10 sont professionnels (répartition déterministe, rejouable)."""
    return index % 10 < PROFESSIONAL_SHARE


def fictitious_vat_number(rng):
    """Numéro de TVA belge fictif, au format valide (BE0 + 7 chiffres + clé modulo 97)."""
    base = rng.randint(2_000_000, 9_999_999)
    head = f"0{base}"
    return f"BE{head}{97 - int(head) % 97:02d}"


def fictitious_company(rng, first_name, last_name):
    """Coordonnées d'entreprise fictives : société (PME) ou indépendant en nom propre."""
    if rng.random() < 0.25:
        company = f"{first_name} {last_name} – {rng.choice(['Maintenance', 'Dépannage industriel', 'Techniek'])}"
    else:
        company = f"{last_name} {rng.choice(ACTIVITIES)} {rng.choice(LEGAL_FORMS)}"
    postal_code, city = rng.choice(CITIES)
    return {
        'company_name': company,
        'vat_number': fictitious_vat_number(rng),
        'street': f"{rng.choice(STREETS)} {rng.randint(1, 250)}",
        'postal_code': postal_code,
        'city': city,
    }
