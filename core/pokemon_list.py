import os
import requests
import json
from table_type import PokemonType  # Import de ta classe personnalisée

# --- CONFIGURATION DES CHEMINS ---
DATA_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\data"
API_URL = "https://pokeapi.co/api/v2/"

class PokeDownloader:
    def __init__(self):
        self.downloaded_ids = set()
        self.all_pokemon_data = {}
        
        # Classifications Spéciales
        self.legendaries = ["kyogre", "groudon", "rayquaza", "mewtwo", "xerneas", "eternatus"]
        self.semi_legendaries = [
            "regirock", "registeel", "regice", "regidrago", "regieleki", "regigigas",
            "heatran", "darkrai", "cobalion", "virizion", "terrakion", "enamorus",
            "xurkitree", "kartana", "pecharunt", "articuno", "moltres", "zapdos",
            "suicune", "entei", "raikou", "buzzwole", "pheromosa", "tapu-koko", 
            "tapu-lele", "tapu-bulu", "tapu-fini"
        ]

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

    def get_fr_info(self, species_name):
        res = requests.get(f"{API_URL}pokemon-species/{species_name}")
        if res.status_code == 200:
            data = res.json()
            name_fr = species_name.capitalize()
            for n in data.get('names', []):
                if n['language']['name'] == 'fr':
                    name_fr = n['name']
                    break
            
            gen_raw = data.get('generation', {}).get('name', 'generation-i')
            romans = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9'}
            gen_num = gen_raw.split('-')[-1]
            gen_folder = f"Generation {romans.get(gen_num, gen_num)}"
            return name_fr, gen_folder
        return species_name.capitalize(), "Generation Inconnue"

    def get_type_fr(self, type_name_en):
        """Traduction des types en français"""
        trad = {
            "normal": "Normal", "fire": "Feu", "water": "Eau", "grass": "Plante", 
            "electric": "Electrik", "ice": "Glace", "fighting": "Combat", "poison": "Poison", 
            "ground": "Sol", "flying": "Vol", "psychic": "Psy", "bug": "Insecte", 
            "rock": "Roche", "ghost": "Spectre", "dragon": "Dragon", "steel": "Acier", 
            "fairy": "Fée", "dark": "Ténèbres"
        }
        try:
            _ = PokemonType() 
        except:
            pass
        return trad.get(type_name_en, type_name_en.capitalize())

    def get_evolution_family(self, species_name, region_suffix=""):
        family = []
        res = requests.get(f"{API_URL}pokemon-species/{species_name}")
        if res.status_code == 200:
            chain_url = res.json()['evolution_chain']['url']
            chain_data = requests.get(chain_url).json()
            def walk(node):
                name = node['species']['name']
                if region_suffix:
                    v_res = requests.get(f"{API_URL}pokemon/{name}{region_suffix}")
                    family.append((f"{name}{region_suffix}", name)) if v_res.status_code == 200 else family.append((name, name))
                else:
                    family.append((name, name))
                for e in node['evolves_to']: walk(e)
            walk(chain_data['chain'])
        return family

    def process_pokemon(self, name_api, species_base):
        # SECURITE : On ne télécharge pas si déjà dans le set
        if name_api in self.downloaded_ids: return
        
        res = requests.get(f"{API_URL}pokemon/{name_api}")
        if res.status_code != 200: return
        pk_data = res.json()
        
        name_fr, gen_folder = self.get_fr_info(species_base)
        stats = {s['stat']['name']: s['base_stat'] for s in pk_data['stats']}
        types_fr = [self.get_type_fr(t['type']['name']) for t in pk_data['types']]
        abilities = [a['ability']['name'].replace("-", " ").capitalize() for a in pk_data['abilities']]

        # Classification
        if species_base in self.legendaries: sub = "Legendaires"
        elif species_base in self.semi_legendaries: sub = "Semi-Legendaires"
        else: sub = gen_folder
        
        self.all_pokemon_data[name_fr] = {
            "id": pk_data['id'],
            "nom_api": name_api,
            "types": types_fr,
            "stats": {
                "hp": stats.get('hp'),
                "attaque": stats.get('attack'),
                "defense": stats.get('defense'),
                "attaque_spe": stats.get('special-attack'),
                "defense_spe": stats.get('special-defense'),
                "vitesse": stats.get('speed')
            },
            "talents": abilities,
            "generation": sub
        }

        self.downloaded_ids.add(name_api)
        print(f"Données extraites : {name_fr} ({sub})")

    def run(self):
        print("--- Démarrage de l'extraction des données JSON ---")
        os.makedirs(DATA_PATH, exist_ok=True)
        
        # 1. Traitement de la liste principale (Starters et liste habituelle)
        for item, api_name in self.fr_to_en.items():
            suffix = ""
            base = api_name
            if "-" in api_name:
                parts = api_name.split("-")
                if parts[-1] in ["alola", "galar", "hisui", "paldea"]:
                    base = parts[0]
                    suffix = "-" + parts[-1]
            
            try:
                family = self.get_evolution_family(base, suffix)
                for m_api, m_species in family:
                    self.process_pokemon(m_api, m_species)
            except:
                self.process_pokemon(api_name, base)

        # 2. SECURITE / AJOUT : Traitement explicite des Légendaires et Semi-Légendaires
        # Au cas où ils ne seraient pas dans la liste fr_to_en ou les familles d'évolution
        for leg in self.legendaries:
            self.process_pokemon(leg, leg)
        
        for semi in self.semi_legendaries:
            self.process_pokemon(semi, semi)

        json_file = os.path.join(DATA_PATH, "pokemon_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_pokemon_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n--- Terminé ! Fichier JSON généré : {json_file} ---")

if __name__ == "__main__":
    downloader = PokeDownloader()
    downloader.run()