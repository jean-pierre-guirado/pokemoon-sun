import os
import requests

# --- CONFIGURATION DES CHEMINS ---
BASE_PATH = r"C:\Users\horus\OneDrive\Desktop\poke fantasy\asset\sprite"
API_URL = "https://pokeapi.co/api/v2/"

# Classifications Spéciales demandées
LEGENDARIES = [
    "kyogre", "groudon", "rayquaza", "mewtwo", "xerneas", "eternatus"
]

SEMI_LEGENDARIES = [
    "regirock", "registeel", "regice", "regidrago", "regieleki", "regigigas",
    "tapu-koko", "tapu-lele", "tapu-bulu", "tapu-fini", "heatran", "darkrai",
    "cobalion", "virizion", "terrakion", "enamorus", "xurkitree", "kartana",
    "pecharunt", "articuno", "moltres", "zapdos", "suicune", "entei", "raikou",
    "buzzwole", "pheromosa"
]

# Dictionnaire de base
FR_TO_EN = {
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

DOWNLOADED_IDS = set()

def get_fr_name_and_gen(species_name):
    res = requests.get(f"{API_URL}pokemon-species/{species_name}")
    if res.status_code == 200:
        data = res.json()
        name_fr = species_name.capitalize()
        for n in data.get('names', []):
            if n['language']['name'] == 'fr':
                name_fr = n['name']
                break
        gen_raw = data.get('generation', {}).get('name', 'generation-ix')
        gen_num = gen_raw.split('-')[-1].upper()
        romans = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9'}
        # Si generation-unknown ou non trouvé dans romans, on met Generation 9 par défaut
        gen_folder = f"Generation {romans.get(gen_num, '9')}"
        return name_fr, gen_folder
    return species_name.capitalize(), "Generation 9"

def download_img(url, folder, filename):
    if not url: return
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    
    # SECURITE : Si le fichier existe déjà, on ne télécharge pas
    if os.path.exists(file_path):
        return

    try:
        r = requests.get(url, timeout=10)
        with open(file_path, 'wb') as f: f.write(r.content)
    except: pass

def process_pokemon(name_api, species_base):
    if name_api in DOWNLOADED_IDS: return
    res = requests.get(f"{API_URL}pokemon/{name_api}")
    if res.status_code != 200: return
    data = res.json()
    
    name_fr, gen_folder = get_fr_name_and_gen(species_base)
    
    # Choix du dossier (en français)
    if species_base.lower() in LEGENDARIES: sub = "Legendaires"
    elif species_base.lower() in SEMI_LEGENDARIES: sub = "Semi-Legendaires"
    else: sub = gen_folder
    
    target_dir = os.path.join(BASE_PATH, sub)
    s = data['sprites']
    
    tasks = [
        (s['front_default'], f"{name_fr}_face.png"),
        (s['back_default'], f"{name_fr}_dos.png"),
        (s['front_shiny'], f"{name_fr}_face_shiny.png"),
        (s['back_shiny'], f"{name_fr}_dos_shiny.png")
    ]

    for url, fname in tasks:
        if url: download_img(url, target_dir, fname)
        elif "face" in fname and "shiny" not in fname:
            download_img(s['other']['official-artwork']['front_default'], target_dir, fname)

    DOWNLOADED_IDS.add(name_api)
    print(f"Vérifié/Enregistré : {name_fr} (Dossier: {sub})")

def run():
    print("--- Démarrage de l'extraction avec sécurité anti-doublon ---")
    
    # 1. Liste du dictionnaire
    for item, api_name in FR_TO_EN.items():
        process_pokemon(api_name, api_name.split("-")[0])

    # 2. Légendaires
    for leg in LEGENDARIES:
        process_pokemon(leg, leg)

    # 3. Semi-Légendaires
    for semi in SEMI_LEGENDARIES:
        process_pokemon(semi, semi)

if __name__ == "__main__":
    run()
    print("\n--- Opération terminée ! ---")