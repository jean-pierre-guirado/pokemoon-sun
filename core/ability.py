import os
import requests
import json

# --- CONFIGURATION DES CHEMINS ---
DATA_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"
API_URL = "https://pokeapi.co/api/v2/"

class AbilityScraper:
    def __init__(self):
        self.downloaded_ids = set()
        self.pokemon_abilities_data = {}
        
        # Classifications Spéciales
        self.legendaries = ["kyogre", "groudon", "rayquaza", "mewtwo", "xerneas", "eternatus"]
        self.semi_legendaries = [
            "regirock", "registeel", "regice", "regidrago", "regieleki", "regigigas",
            "heatran", "darkrai", "cobalion", "virizion", "terrakion", "enamorus",
            "xurkitree", "kartana", "pecharunt", "articuno", "moltres", "zapdos",
            "suicune", "entei", "raikou", "buzzwole", "pheromosa", "tapu-koko", 
            "tapu-lele", "tapu-bulu", "tapu-fini"
        ]

        # Ton dictionnaire de référence pour maintenir la cohérence
        self.fr_to_en = {
            "bulbizarre": "bulbasaur", "salameche": "charmander", "carapuce": "squirtle",
            "germignon": "chikorita", "hericendre": "cyndaquil", "kaiminus": "totodile",
            "arcko": "treecko", "poussifeu": "torchic", "gobou": "mudkip",
            "tortipouss": "turtwig", "ouisticram": "chimchar", "tiplouf": "piplup",
            "vipelierre": "snivy", "gruikui": "tepig", "moustillon": "oshawott",
            "marisson": "chespin", "feunnec": "fennekin", "grenousse": "froakie",
            "brindibou": "rowlet", "flamiaou": "litten", "otaquin": "popplio",
            "ouistempo": "grookey", "flambino": "scorbunny", "larmeleon": "sobble",
            "poussacha": "sprigatito", "chochodile": "fuecoco", "coiffeton": "quaxly",
            "exagide": "aegislash-shield", "tarsal": "ralts", "monaflemit": "slaking",
            "ectoplasma": "gengar", "lucario": "lucario", "absol": "absol",
            "scalpion": "pawniard", "metalosse": "metagross", "tyranocif": "tyranitar",
            "cisayox": "scizor", "chenipan": "caterpie", "chenipotte": "wurmple",
            "stalgamin": "snorunt", "airmure": "skarmory", "draby": "bagon",
            "archeodon": "bronzong", "ptera": "aerodactyl", "racaillou": "geodude",
            "nodulithe": "roggenrola", "nemelios": "pyroar", "coxy": "ledyba",
            "smogo": "koffing", "gloupti": "gulpin", "dynavolt": "electrike",
            "elekid": "elekid", "magby": "magby", "voltorbe": "voltorb",
            "seviper": "seviper", "mangriff": "zangoose", "abo": "ekans",
            "medhyena": "poochyena", "zigzaton": "zigzagoon", "zigzaton-de-galar": "zigzagoon-galar",
            "limonde": "stunfisk", "limonde-de-galar": "stunfisk-galar", "ponyta": "ponyta",
            "ponyta-de-galar": "ponyta-galar", "scrutella": "gothita", "abra": "abra",
            "chartor": "torkoal", "magneti": "magnemite", "kabuto": "kabuto",
            "grindur": "ferroseed", "steelix": "steelix", "amonita": "omanyte",
            "pichu": "pichu", "magicarpe": "magikarp", "grainipiot": "seedot",
            "rattata-dalola": "rattata-alola", "carapagos": "tirtouga", "flabebe": "flabebe",
            "arkeapti": "archen", "goupix": "vulpix", "goupix-dalola": "vulpix-alola",
            "draieul": "drampa", "parecool": "slakoth", "vorasterie": "mareanie",
            "sabelette": "sandshrew", "sabelette-dalola": "sandshrew-alola", "mimiqui": "mimikyu",
            "pikachu": "pikachu", "tibouder": "mudbray", "garde-de-fer": "iron-valiant",
            "darumarond": "darumaka", "passerouge": "fletchling", "tadmorv": "grimer",
            "tadmorv-dalola": "grimer-alola", "zorua-dhisui": "zorua-hisui", "roue-de-fer": "iron-treads",
            "forgerette": "tinkatink", "flotte-meche": "flutter-mane", "funecire": "litwick",
            "miaouss": "meowth", "tritox": "salandit", "paume-de-fer": "iron-hands",
            "vrombi": "varoom", "fort-ivoire": "great-tusk", "morpheo": "castform",
            "kecleon": "kecleon", "frigodo": "frigibax", "hurle-queue": "scream-tail",
            "ptyranidur": "tyrunt", "miaouss-dalola": "meowth-alola", "rototaupe": "drilbur",
            "miaouss-de-galar": "meowth-galar", "hydragon": "dracovish", "fantyrm": "dreepy",
            "croquine": "steenee", "nounourson": "stufful", "sovkipou": "wimpod",
            "duralugon": "duraludon", "grelacon": "bergmite", "charbi": "rolycoly",
            "larvibule": "grubbin", "minisange": "rookidee", "grimalin": "impidimp",
            "hexadron": "falinks", "bibichut": "hatenna", "verpom": "applin",
            "galbagla": "eiscue-ice", "galvagon": "dracozolt", "hydragla": "arctovish",
            "mordudor": "gimmighoul", "charbambin": "charcadet", "chinchidou": "minccino",
            "nenupiot": "lotad", "cadoizo": "delibird", "feuforeve": "misdreavus",
            "machoc": "machop", "axoloto": "wooper", "ferosinge": "mankey",
            "rattata": "rattata", "lippouti": "smoochum", "scarabrute": "pinsir",
            "axoloto-de-paldea": "wooper-paldea", "corboss": "honchkrow", "debugant": "tyrogue",
            "pyronille": "larvesta", "sorbebe": "vanillite", "marcacrin": "swinub",
            "goelise": "wingull", "coupenotte": "axew", "melo": "cleffa",
            "furaiglon": "rufflet", "solochi": "deino", "makuhita": "makuhita",
            "azurill": "azurill", "mysdibule": "mawile", "zebibron": "blitzle",
            "ponchiot": "lillipup", "charpenti": "timburr", "baggiguane": "scraggy",
            "tenefix": "sableye", "galekid": "aron", "carvanha": "carvanha",
            "barloche": "barboach", "judokrak": "throh", "blizzi": "snover",
            "cradopaud": "croagunk", "anorith": "anorith", "ptiravi": "happiny",
            "lilia": "lileep", "relicanth": "relicanth", "dinoclier": "shieldon",
            "kranidos": "cranidos", "rozbouton": "budew", "spiritomb": "spiritomb",
            "laporeille": "buneary", "griknot": "gible"
        }

    def get_fr_name(self, species_name):
        """Récupère le nom français du Pokémon via species"""
        res = requests.get(f"{API_URL}pokemon-species/{species_name}")
        if res.status_code == 200:
            data = res.json()
            for n in data.get('names', []):
                if n['language']['name'] == 'fr':
                    return n['name']
        return species_name.capitalize()

    def get_ability_details(self, url):
        """Récupère le nom FR et la description FR d'un talent"""
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            nom_fr = next((n['name'] for n in data['names'] if n['language']['name'] == 'fr'), data['name'])
            desc_fr = next((e['short_effect'] for e in data['effect_entries'] if e['language']['name'] == 'fr'), 
                           "Description non disponible.")
            return nom_fr, desc_fr
        return None, None

    def process_pokemon_abilities(self, name_api, species_base):
        if name_api in self.downloaded_ids: return
        res = requests.get(f"{API_URL}pokemon/{name_api}")
        if res.status_code != 200: return
        
        pk_data = res.json()
        name_fr_pk = self.get_fr_name(species_base)
        
        abilities_list = []
        raw_abilities = pk_data['abilities']
        
        normal_slots = [a for a in raw_abilities if not a['is_hidden']]
        prob_normal = 100 if len(normal_slots) == 1 else 50

        for ab in raw_abilities:
            n_fr, d_fr = self.get_ability_details(ab['ability']['url'])
            
            ability_info = {
                "nom": n_fr,
                "description": d_fr,
                "slot": ab['slot'],
                "is_hidden": ab['is_hidden'],
                "probabilite": "60%" if ab['is_hidden'] else f"{prob_normal}%"
            }
            abilities_list.append(ability_info)

        self.pokemon_abilities_data[name_fr_pk] = {
            "id": pk_data['id'],
            "nom_api": name_api,
            "talents": abilities_list
        }
        
        self.downloaded_ids.add(name_api)
        print(f"Extraction talents réussie : {name_fr_pk}")

    def run(self):
        print("--- Démarrage de l'extraction des Talents et Probabilités ---")
        os.makedirs(DATA_PATH, exist_ok=True)
        
        # 1. Traitement de la liste fr_to_en
        for item, api_name in self.fr_to_en.items():
            base = api_name
            if "-" in api_name:
                parts = api_name.split("-")
                if parts[-1] in ["alola", "galar", "hisui", "paldea"]:
                    base = parts[0]
            self.process_pokemon_abilities(api_name, base)

        # 2. Sécurité : Ajout explicite des légendaires et semi-légendaires
        for leg in self.legendaries:
            self.process_pokemon_abilities(leg, leg)
        
        for semi in self.semi_legendaries:
            self.process_pokemon_abilities(semi, semi)

        json_file = os.path.join(DATA_PATH, "pokemon_abilities_full.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.pokemon_abilities_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n--- Terminé ! JSON généré : {json_file} ---")

if __name__ == "__main__":
    scraper = AbilityScraper()
    scraper.run()