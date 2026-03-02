================================================================================
                         POKE FANTASY — SHINY EDITION
                              README & DOCUMENTATION
                                Version Finale
================================================================================

Table des matières :
  1. Présentation du projet
  2. Prérequis & bibliothèques
  3. Architecture des fichiers
  4. Structure des dossiers assets & data
  5. Modules détaillés (classes, méthodes, logique)
  6. Flux de jeu complet
  7. Systèmes de jeu
  8. Données JSON
  9. Résumé des fonctionnalités


================================================================================
  1. PRÉSENTATION DU PROJET
================================================================================

Poke Fantasy – Shiny Edition est un jeu RPG de combat Pokémon fait entièrement
en Python avec la bibliothèque Arcade. Il comprend :

  - Un menu principal avec système de sauvegarde 3 slots
  - Une séquence d'introduction (création de personnage, choix du starter)
  - Un système de stages de combat (1 à 99 + boss final au stage 100)
  - Des combats Pokémon au tour par tour avec mécaniques complètes
  - Un Pokédex, une boutique inter-stage, un système monétaire
  - Des dresseurs IA, un boss final unique avec IA stratégique avancée
  - Des backgrounds dynamiques selon le type du Pokémon ennemi
  - Un écran de victoire finale (wing.png + CONGRATULATIONS)


================================================================================
  2. PRÉREQUIS & BIBLIOTHÈQUES
================================================================================

Python : 3.10 ou supérieur (utilise les annotations de type modernes)

Bibliothèques Python utilisées :
-------------------------------

  arcade          - Moteur graphique 2D, gestion des fenêtres, des textures,
                    de l'audio, des inputs clavier et des animations.
                    Utilisé dans : main.py, intro.py, test.py, dresseur.py, boss.py
                    Site : https://api.arcade.academy

  json            - Lecture et écriture des fichiers de données (.json).
                    Utilisé dans : tous les modules pour charger/sauvegarder
                    les données Pokémon, capacités, évolutions, sauvegardes.

  os              - Manipulation des chemins de fichiers et dossiers,
                    vérification d'existence de fichiers (os.path.exists),
                    suppression de fichiers (os.remove).
                    Utilisé dans : tous les modules.

  random          - Génération aléatoire pour les combats, le taux shiny,
                    le choix des Pokémon ennemis, les dégâts, les captures,
                    les natures, les noms de dresseurs.
                    Utilisé dans : capture.py, engines.py, dresseur.py, boss.py,
                                   test.py, intro.py.

  math            - Calculs mathématiques pour les stats Pokémon, les animations
                    (sinus/cosinus), les formules d'expérience et d'évolution.
                    Utilisé dans : engines.py, models.py, intro.py, dresseur.py.

  unicodedata     - Normalisation des caractères Unicode (suppression des accents)
                    pour comparer des noms Pokémon de manière robuste.
                    Utilisé dans : utils.py (fonction normaliser).

  sys             - Manipulation de sys.path pour ajouter les dossiers d'imports
                    dynamiquement selon l'emplacement du script.
                    Utilisé dans : main.py, config.py.

  requests        - Appels HTTP vers l'API PokéAPI pour télécharger les données
                    des capacités Pokémon et les sprites.
                    Utilisé dans : fetch_moves.py, sprite_download.py.

  pathlib         - Manipulation orientée objet des chemins de fichiers.
                    Utilisé dans : fetch_moves.py, sprite_download.py.

  time            - Pauses et gestion temporelle lors du téléchargement des assets.
                    Utilisé dans : sprite_download.py.

  urllib.request  - Téléchargement des sprites PNG depuis des URLs distantes.
                    Utilisé dans : sprite_download.py.

  concurrent.futures - Téléchargement parallèle des sprites (ThreadPoolExecutor)
                    pour accélérer la récupération des assets.
                    Utilisé dans : sprite_download.py.


================================================================================
  3. ARCHITECTURE DES FICHIERS
================================================================================

poke fantasy/
│
├── main.py                  ← Point d'entrée, menu principal
│
├── core/                    ← Tous les modules du jeu
│   ├── config.py            ← Chemins et constantes globales
│   ├── models.py            ← Classe Pokemon + NatureEngine (dans le même fichier)
│   ├── engines.py           ← LevelEngine, ExperienceEngine, CombatEngine,
│   │                           StatusEngine, ItemEngine
│   ├── turn_manager.py      ← TurnManager (logique tour par tour)
│   ├── capture.py           ← CaptureEngine (formule de capture)
│   ├── table_type.py        ← TypeChart (table des types, 18 types)
│   ├── nature.py            ← NatureEngine (24 natures, multiplicateurs)
│   ├── pokedex.py           ← PokedexManager (lecture/écriture pokedex.json)
│   ├── utils.py             ← normaliser() (utilitaire unicode)
│   ├── monnaie.py           ← MonnaieEngine (système monétaire POO)
│   ├── dresseur.py          ← DresseurIA (dresseur ennemi IA)
│   ├── boss.py              ← BossIA (boss final stage 100)
│   ├── intro.py             ← IntroView (séquence de création de personnage)
│   └── test.py              ← PokeFantasyGame (boucle de jeu principale)
│
├── data/                    ← Fichiers JSON de données
│   ├── pokemon_data.json    ← Stats de base de tous les Pokémon
│   ├── capacite_list.json   ← Liste de toutes les capacités
│   ├── evolution_config.json← Règles d'évolution par niveau
│   ├── dresseur_config.json ← Configuration courante du joueur (sync)
│   ├── pokedex.json         ← Pokémons rencontrés/capturés (généré en jeu)
│   └── status_data.json     ← Labels et couleurs des statuts
│
├── saves/                   ← Sauvegardes des 3 slots
│   ├── slot_1.json
│   ├── slot_2.json
│   └── slot_3.json
│
└── asset/
    ├── sprite/              ← Sprites Pokémon (_face.png, _dos.png, _shiny_face.png...)
    ├── NPC/                 ← Images des personnages
    │   ├── professor.png    ← Professeur de l'intro
    │   ├── garcon.png       ← Avatar joueur masculin
    │   ├── fille.png        ← Avatar joueur féminin
    │   ├── dresseur.png     ← Dresseur ennemi (variante 1)
    │   ├── dresseur_2.png   ← Dresseur ennemi (variante 2)
    │   ├── dresseur_3.png   ← Dresseur ennemi (variante 3)
    │   ├── dresseur_4.png   ← Dresseur ennemi (variante 4)
    │   ├── dresseur_5.png   ← Dresseur ennemi (variante 5)
    │   └── boss.png         ← Boss final
    ├── audio/               ← Musiques
    │   ├── intro.mp3        ← Musique de l'écran d'introduction
    │   ├── battle_theme.mp3 ← Musique de combat normale
    │   └── final.mp3        ← Musique du combat boss stage 100
    ├── types/               ← Icônes de types Pokémon
    │   ├── acier.png, combat.png, dragon.png, eau.png, electrick.png,
    │   │   fee.png, feu.png, glace.png, insecte.png, Normal.png,
    │   │   plante.png, poison.png, psy.png, roche.png, sol.png,
    │   │   spectre.png, tenebres.png, vol.png
    ├── objet/               ← Images des objets (balls, potions...)
    ├── fonts/               ← Backgrounds et images d'interface
    │   ├── logo.jpg         ← Logo du menu principal
    │   ├── main.png         ← Background menu principal
    │   ├── glace.png        ← Background Eau / Glace
    │   ├── labo.jpg         ← Background Psy / Électrik
    │   ├── prairie.jpg      ← Background Normal / Fée
    │   ├── volcan.jpg       ← Background Sol / Feu / Roche / Acier
    │   ├── jungle.png       ← Background Insecte / Plante
    │   ├── sommet.png       ← Background Combat / Dragon / Vol
    │   ├── manoir.png       ← Background Spectre / Ténèbres / Poison
    │   ├── arene.jpg        ← Background combat Dresseur et Boss
    │   └── wing.png         ← Image de l'écran de victoire finale


================================================================================
  4. STRUCTURE DES DOSSIERS ASSETS & DATA
================================================================================

SPRITES (asset/sprite/)
-----------------------
Chaque Pokémon possède jusqu'à 4 sprites :
  - NomPokemon_face.png        : vue de face (combat, ennemi)
  - NomPokemon_dos.png         : vue de dos (joueur qui attaque)
  - NomPokemon_shiny_face.png  : version shiny de face
  - NomPokemon_shiny_dos.png   : version shiny de dos

Les sprites sont organisés en sous-dossiers par Pokémon.
Téléchargés automatiquement via sprite_download.py depuis PokéAPI.

POKÉMON DATA (data/pokemon_data.json)
--------------------------------------
Structure d'une entrée :
  {
    "Flamiaou": {
      "types": ["Feu"],
      "stats": {
        "hp": 45, "attaque": 48, "defense": 45,
        "attaque_spe": 60, "defense_spe": 65, "vitesse": 45
      },
      "learnset": {
        "1": "Griffe", "5": "Flammèche", "12": "Rugissement"
      }
    }
  }

CAPACITÉS (data/capacite_list.json)
-------------------------------------
Structure d'une entrée :
  {
    "nom_attaque": "Flammèche",
    "type": "Feu",
    "categorie": "Special",
    "puissance": 40,
    "precision": 100,
    "effet": "BURN",
    "chance_effet": 10,
    "stat_touchee": null,
    "valeur_stat": 0
  }

Catégories possibles : "Physique", "Special", "Status"
Effets possibles : "DAMAGE", "BURN", "PARALYZE", "SLEEP", "TOXIC", "POISON",
                   "HEAL_SELF", "BOOST_SELF", "DEBUFF_ENEMY"

ÉVOLUTIONS (data/evolution_config.json)
-----------------------------------------
Structure :
  {
    "flamiaou": {
      "methode": "level",
      "valeur": 16,
      "cible": "Felinflam"
    }
  }
  Ou pour les évolutions multiples (branching) :
  {
    "evoli": [
      {"methode": "level", "valeur": 25, "cible": "Voltali"},
      {"methode": "level", "valeur": 25, "cible": "Pyroli"}
    ]
  }


================================================================================
  5. MODULES DÉTAILLÉS
================================================================================

────────────────────────────────────────────────────────────────────────────────
  config.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Centralise tous les chemins de fichiers et les constantes globales.
       Ajoute BASE_PATH et core/ à sys.path automatiquement.

Constantes exportées :
  BASE_PATH         - Racine du projet (chemin absolu)
  DATA_PATH         - Dossier data/
  ASSET_PATH        - Dossier asset/
  SAVES_PATH        - Dossier saves/ (créé automatiquement si absent)
  SPRITE_PATH       - asset/sprite/
  TYPE_ICON_PATH    - asset/types/
  OBJET_PATH        - asset/objet/
  AUDIO_PATH        - asset/audio/
  DRESSEUR_JSON     - data/dresseur_config.json
  CAPA_JSON         - data/capacite_list.json
  POKEDEX_JSON      - data/pokedex.json
  POKEMON_DATA_JSON - data/pokemon_data.json
  EVOLUTION_JSON    - data/evolution_config.json
  BATTLE_THEME_PATH - asset/audio/battle_theme.mp3
  SCREEN_WIDTH      - 800 (pixels)
  SCREEN_HEIGHT     - 600 (pixels)
  SCREEN_TITLE      - "Poke Fantasy - Shiny Edition"
  STATUS_DATA       - Dict des labels/couleurs des statuts (Brûlure, Paralysie...)


────────────────────────────────────────────────────────────────────────────────
  utils.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Utilitaires communs partagés par tous les modules.

  def normaliser(txt: str) -> str
    Supprime les accents, met en minuscules, retire les espaces superflus.
    Utilise unicodedata.normalize('NFD') pour décomposer les caractères accentués.
    Exemple : normaliser("Flammèche") → "flammeche"
    Utilisé partout pour comparer des noms Pokémon indépendamment de la casse
    et des accents (noms dans les JSON vs noms affichés).


────────────────────────────────────────────────────────────────────────────────
  models.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Définit la classe centrale Pokemon et la classe NatureEngine.

CLASS : Pokemon
  Représente un Pokémon instancié en mémoire avec toutes ses données de combat.

  Attributs :
    nom             - Nom affiché (ex: "Flamiaou", "Flamiaou Shiny")
    nature          - Nom de la nature (ex: "Brave")
    niveau          - Niveau actuel (1-100)
    hp_base         - Points de vie maximum
    hp              - Points de vie actuels
    xp              - XP accumulée sur le niveau actuel
    xp_max          - XP requise pour le prochain niveau (niveau * 100)
    statut          - Statut actuel : None, "Brûlure", "Paralysie",
                                      "Poison", "Toxique", "Sommeil", "Gelé"
    types           - Liste de types (ex: ["Feu", "Vol"])
    stats           - Dict {"attaque", "defense", "vitesse",
                            "attaque_spe", "defense_spe"}
    stages          - Dict de modificateurs de combat (-6 à +6) pour chaque stat
    compteur_toxic  - Compteur pour le dégât progressif du statut Toxique
    capacites_noms  - Liste des noms de capacités (max 4)
    moves_obj       - Liste des dicts complets de capacités (chargés depuis db_capas)
    poke_data_map   - Référence à la base de données Pokémon
    db_capas        - Référence à la base de données des capacités

  Méthodes :
    __init__(data, db_capas, poke_data_map)
      Construit un Pokémon depuis un dict. Charge les types depuis poke_data_map
      si disponible (priorité aux données de la BDD sur le dict).

    refresh_moves_obj()
      Recharge moves_obj depuis capacites_noms en cherchant dans db_capas.
      Crée un move de fallback (40 puissance, Normal) si une capacité est inconnue.

    gain_xp(montant) → list[str]
      Ajoute de l'XP, gère les level-ups en boucle (plusieurs niveaux possibles
      d'un coup). Appelle LevelEngine.recalculer_stats() à chaque niveau.
      Retourne un journal textuel des gains (ex: ["Niv 12: +15 HP, +3 ATK"]).

    verifier_nouvelle_capacite() → str | None
      Cherche dans le learnset si le Pokémon apprend une capacité au niveau actuel.
      Si l'équipe est pleine (4 capacités), remplace la première.
      Retourne le nom de la capacité apprise ou None.

    to_dict() → dict
      Sérialise le Pokémon en dict JSON-compatible pour la sauvegarde.

CLASS : NatureEngine (dans models.py, aussi dans nature.py)
  Gère les 24 natures Pokémon et leurs effets sur les stats.

  DATA (dict de classe)
    Mappe chaque nature à un tuple (stat_boostée, stat_nerfée).
    24 natures incluant : Brave, Modeste, Timide, Rigide, Assuré, Relax,
    Calme, Jovial, Malin, Solo, Hardi (neutre), Docile (neutre), etc.

  get_multiplier(nature_name, stat_name) → float
    Retourne 1.1 si la stat est boostée, 0.9 si nerfée, 1.0 sinon.

  apply_nature_to_stats(nature_name, stats) → dict
    Applique les multiplicateurs de nature à un dict complet de stats.
    Gère le mapping anglais/français (attaque → Attaque, etc.).


────────────────────────────────────────────────────────────────────────────────
  engines.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Moteurs de jeu regroupés (niveau, XP, combat, statuts, objets).

CLASS : LevelEngine
  Gère la montée de niveau et le recalcul des stats.

  recalculer_stats(p_data, poke_data_map) → dict
    Formule HP  : floor((2 * base_hp * niveau) / 100) + niveau + 10
    Formule stat: floor((2 * base_stat * niveau) / 100) + 5
    Met à jour p_data en place. Retourne les gains par stat.
    HP actuels augmentent proportionnellement aux HP max gagnés.

CLASS : ExperienceEngine

  calculer_xp_gagne(ennemi) → int
    Formule : ennemi.niveau * random.randint(15, 25)
    Simple, rapide, donne environ 15-25 XP par niveau de l'ennemi.

CLASS : CombatEngine
  Calcule les dégâts et applique les effets secondaires des capacités.

  _get_stat_multiplicateur(stage) → float
    Convertit un stage de combat (-6 à +6) en multiplicateur :
    stage >= 0 : (2 + stage) / 2
    stage < 0  : 2 / (2 + abs(stage))

  _get_stat_actuelle(pokemon, stat_nom) → float
    Stat réelle = stats[stat_nom] * multiplicateur(stages[stat_nom])

  calculer_degats(attaquant, defenseur, move_data) → tuple
    Gère : paralysie (25% raté), précision (random), coup critique (6.25%),
    STAB (x1.5 si même type), multiplicateur de type, variation aléatoire (0.85-1.0),
    réduction d'attaque si brûlé (x0.5).
    Formule dégâts :
      brut = ((2*niveau/5 + 2) * puissance * (ATK/DEF) / 50) + 2
      final = brut * critique * variation * STAB * mult_type
    Retourne : (dégâts, mult_type, critique, raté, message)

CLASS : StatusEngine
  Gère l'application et les effets des statuts.

  modifier_stage(p, stat, quantite)
    Modifie un stage de combat (clamped entre -6 et +6).

  appliquer_effet_technique(attaquant, defenseur, capa)
    Gère tous les effets non-dommages : HEAL_SELF, BOOST_SELF, DEBUFF_ENEMY,
    Danse Lames (+2 ATK), Machination (+2 ATK_SPE), Rugissement (-1 ATK ennemi),
    TOXIC, POISON, BURN, PARALYZE. Respecte le taux chance_effet.

  gerer_fin_de_tour(p)
    Brûlure : -1/16 HP max par tour
    Poison  : -1/8 HP max par tour
    Toxique : -compteur/16 HP max (croissant, max 15/16 au tour 15)

CLASS : ItemEngine
  Applique les effets des objets de soin.

  utiliser_objet(item_nom, pokemon) → (bool, str)
    Bonbon Rare : level-up immédiat
    Potion      : +20 HP (refuse si KO ou full PV)
    Super Potion : +50 HP
    Hyper Potion : +200 HP
    Max Potion  : PV max complets
    Rappel      : Revive à HP_max / 2 (refuse si pas KO)
    Max Rappel  : Revive à HP max complets


────────────────────────────────────────────────────────────────────────────────
  turn_manager.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Orchestre les tours de combat (ordre, attaques, effets fin de tour).

CLASS : TurnManager

  determiner_ordre(p1, p2, move1, move2) → (premier, second)
    Priorité des capacités d'abord (champ "priorite" dans la capacité).
    Puis comparaison des vitesses (avec -50% si paralysé).
    Égalité → aléatoire.

  executer_attaque(attaquant, defenseur, move) → str
    Vérifie si l'attaquant peut agir (KO, paralysé, endormi, gelé).
    Appelle CombatEngine.calculer_degats(), applique les dégâts sur defenseur.hp.
    Construit et retourne le message de combat.

  executer_tour_complet(joueur, ennemi, move_j, move_e) → str
    Détermine l'ordre, exécute les deux attaques (si le second est encore vivant),
    puis applique les effets de fin de tour pour les deux Pokémon.
    Retourne le journal complet du tour.

  appliquer_effets_fin_de_tour(pokemon) → str
    Brûlure : -max(1, hp_base//16) PV
    Poison  : -max(1, hp_base//8) PV
    Toxique : compteur incrémenté, -max(1, (hp_base//16)*compteur) PV
    Retourne le message de dégâts ou chaîne vide.


────────────────────────────────────────────────────────────────────────────────
  capture.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Moteur de capture Pokémon avec formule fidèle aux jeux.

CLASS : CaptureEngine

  BALL_RATES (dict de classe)
    Multiplicateurs par type de ball :
      master-ball : 2.0 (capture garantie via flag)
      ultra-ball  : 2.0
      great-ball  : 1.5
      poke-ball   : 1.0
      quick-ball  : 2.0 (bonus x4 au tour 1)
      timer-ball  : augmente avec les tours (max x4)

  tenter_capture(ball_nom, ennemi, tour) → (bool, str)
    Master Ball : capture garantie sans calcul.
    Quick Ball  : x4 si tour == 1.
    Timer Ball  : min(4.0, 1.0 + tour*0.3)
    Ratio PV    : 1.0 - (hp_ratio * 0.7) → entre 0.3 (plein) et 1.0 (KO)
    Statut      : Sommeil/Gelé x2.0, Paralysie/Brûlure/Poison x1.5
    Niveau      : malus = max(0.4, 1.0 - niveau*0.005)
    Chance finale = min(0.95, 0.25 * ball_mult * pv_bonus * statut * niveau_malus)
    Retourne (succès, message) avec nombre de secousses si échec.


────────────────────────────────────────────────────────────────────────────────
  table_type.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Table des types complète (génération 6+, 18 types, Fée inclus).

CLASS : TypeChart

  TYPE_NORMALIZE (dict de classe)
    Mappe toute variante de nom de type (anglais, français, avec accents, sans)
    vers le format interne français canonique.
    Exemples : "fire" → "Feu", "electrick" → "Électrik", "tenebres" → "Ténèbres"

  DATA (dict de classe)
    Table d'efficacité complète : DATA[type_attaque][type_defenseur] → float
    Valeurs : 0.0 (immunité), 0.5 (résistance), 1.0 (normal), 2.0 (super efficace)
    18 types × jusqu'à 18 défenseurs possibles.

  get_multiplier(move_type, defender_types) → float
    Normalise les deux types, multiplie les efficacités pour les doubles types.
    Court-circuite à 0.0 dès qu'une immunité est trouvée.

  get_effectiveness_message(multiplier) → str
    >= 1.9 : "C'est super efficace !"
    0.0    : "Ça n'affecte pas l'ennemi..."
    <= 0.6 : "Ce n'est pas très efficace..."


────────────────────────────────────────────────────────────────────────────────
  nature.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Gestion standalone des natures (aussi présent dans models.py).

CLASS : NatureEngine
  24 natures avec leurs effets (+10% / -10% sur une stat).
  Natures neutres (aucun effet) : Hardi, Docile, Sérieux, Pudique, Bizarre.

  Exemples de natures :
    Brave   → ATK +10%, Vitesse -10%
    Modeste → ATK_SPE +10%, ATK -10%
    Timide  → Vitesse +10%, ATK -10%
    Rigide  → ATK +10%, ATK_SPE -10%
    Assuré  → DEF +10%, ATK -10%


────────────────────────────────────────────────────────────────────────────────
  pokedex.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Gestion du fichier pokedex.json (Pokémon rencontrés et capturés).

CLASS : PokedexManager

  Structure JSON du Pokédex :
    {
      "pokemon_rencontres": [
        {
          "nom":         "Flamiaou",
          "hp_base":     55,
          "attaque":     18,
          "defense":     14,
          "vu":          true,
          "possede":     false,
          "description": "Vu dans la nature."
        }
      ]
    }

  charger_pokedex() → dict
    Charge le JSON. Compatible avec l'ancien format liste (conversion auto).
    Retourne {"pokemon_rencontres": []} si le fichier est absent ou corrompu.

  sauvegarder_pokedex(data)
    Écrit le dict dans POKEDEX_JSON avec indent=4.

  enregistrer(pokemon, capture=False)
    Si le Pokémon n'existe pas encore : crée une nouvelle entrée.
    Si il existe : met vu=True, et si capture=True met possede=True.
    Un Pokémon libéré après capture compte quand même comme possede=True.


────────────────────────────────────────────────────────────────────────────────
  monnaie.py  (core/monnaie.py)
────────────────────────────────────────────────────────────────────────────────
Rôle : Système monétaire en PokéDollars (POO statique).

CLASS : MonnaieEngine

  Constantes :
    BASE_PAR_NIVEAU = 15      (PokéDollars de base par niveau ennemi)
    MULT_DRESSEUR   = 2.5     (x2.5 pour un dresseur)
    MULT_SAUVAGE    = 1.0     (x1.0 pour un sauvage)
    BONUS_PAR_STAGE = 0.08    (+8% de gain par stage de progression)

  calculer_gain(ennemi, est_dresseur, stage) → int
    gain = BASE * niveau * mult_type * (1 + (stage-1)*0.08) * variation(0.8-1.2)
    Minimum garanti : 10 PokéDollars.

  calculer_gain_dresseur(equipe_dresseur, stage) → int
    Somme des gains de chaque Pokémon de l'équipe du dresseur.

  crediter(dresseur_data, montant) → int
    Ajoute montant à dresseur_data["argent"]. Retourne le nouveau solde.

  debiter(dresseur_data, montant) → (bool, int)
    Si solde >= montant : débite et retourne (True, nouveau_solde).
    Sinon : retourne (False, solde_actuel).

  formater_message(gain, est_dresseur) → str
    Retourne "Vous remportez XP grâce au dresseur/combat !"


────────────────────────────────────────────────────────────────────────────────
  dresseur.py  (core/dresseur.py)
────────────────────────────────────────────────────────────────────────────────
Rôle : IA Dresseur ennemi avec dialogue, animation et équipe stratégique.

Images : Choisie aléatoirement parmi dresseur.png à dresseur_5.png.

PHRASES_DRESSEUR (3 phrases cultes) :
  - "Bonjour, j'aime les shorts."
  - "Salut tu n'aurais pas une clope ?"
  - Le discours complet d'Eddy Malou et la congolexicomatisation.

NATURES_PAR_ROLE (dict)
  Associe un rôle à une liste de natures optimales :
    attaquant_physique : Brave, Rigide, Solo, Mauvais
    attaquant_special  : Modeste, Foufou, Discret
    tank               : Assuré, Lâche, Relax, Malin
    speedster          : Timide, Naïf, Presse, Jovial

CLASS : DresseurIA
  PROBA_APPARITION = 0.20 (20% de chance par stage)
  VITESSE_GLISSEMENT = 18 (pixels par frame pour l'animation de sortie)

  Attributs d'état :
    nom, titre          - Générés aléatoirement (18 prénoms × 9 titres)
    phrase              - Une des 3 phrases cultes
    equipe              - Liste de 3 instances Pokemon
    soins_restants      - Compteur de guérisons (2 max)
    pokemon_actif       - Référence au Pokemon actuellement en jeu
    seuil_soin          - 0.35 (utilise un soin si PV < 35%)
    anim_phase          - "DIALOGUE" | "GLISSEMENT" | "COMBAT"
    sprite_x            - Position X du sprite (part à 400, sort à 1050)
    dialogue_page       - Page courante du dialogue (3 lignes par page)

  doit_apparaitre() [statique]
    random.random() < 0.20

  Construction équipe :
    _niveau_pour_stage() → int
      base = 2 + (stage-1) * (95/98)  (stage 1 → niv 2, stage 99 → niv 95)
      + random.randint(0, 1) pour varier

    _seuil_evolution(nom_fr) → int | None
      Cherche dans evolution_config si ce Pokémon s'obtient par évolution de niveau.
      Retourne le niveau minimum requis pour l'obtenir (ex: Mammochon nécessite niv 33).

    _choisir_pokemon_candidats(niveau_cible, n=12)
      Filtre tous les Pokémon de poke_data_map en excluant ceux dont le seuil
      d'évolution est supérieur au niveau cible. Évite les formes finales trop tôt.

    _determiner_role(data) → str
      Vitesse > 90 → speedster
      Défense > 85 → tank
      ATK_SPE > ATK + 10 → attaquant_special
      Sinon → attaquant_physique

    _choisir_attaques_strategiques(types, role) → list
      STAB puissance ≥ 60 (2 slots), couverture puissance ≥ 70, statuts utiles.
      Adapté au rôle : attaquants spéciaux priorisent les capacités Special.

  IA de combat :
    choisir_action(ennemi_joueur) → dict
      Si PV < 35% et soins disponibles → {"type": "soin"}
      Sinon → {"type": "attaque", "move": meilleure_attaque}

    _meilleure_attaque(attaquant, defenseur) → dict
      Score = puissance × mult_type × STAB
      Statuts de contrôle (PARALYZE, SLEEP, TOXIC si pas déjà affecté) → score 80
      BOOST_SELF → score 60

    utiliser_soin() → str
      Restaure max(30, hp_base // 2) PV. Décrémente soins_restants.

    changer_pokemon() → bool
      Switch vers le prochain Pokémon vivant qui n'est pas l'actif actuel.

  Dialogue & animation :
    _wrap(texte, max_chars=52) → list
      Découpe le texte en lignes de 52 caractères max. Résultat mis en cache.

    avancer_dialogue() → bool
      Avance d'une page. Si dernière page → anim_phase = "GLISSEMENT". Retourne True si fini.

    update_glissement() → bool
      sprite_x += 18 pixels par frame. True quand hors écran (≥ 1050).

    draw(screen_w, screen_h)
      Dessine le sprite centré (max 220×300px, ratio conservé).
      En phase DIALOGUE : boite de texte en bas avec nom, lignes, numéro de page.


────────────────────────────────────────────────────────────────────────────────
  boss.py  (core/boss.py)
────────────────────────────────────────────────────────────────────────────────
Rôle : Boss final du stage 100 avec IA ultra-stratégique.

Fichiers :
  BOSS_IMG         = asset/NPC/boss.png
  BOSS_MUSIC_PATH  = asset/audio/final.mp3
  BOSS_BG_PATH     = asset/fonts/arene.jpg
  DRESSEUR_BG_PATH = asset/fonts/arene.jpg

Phrase unique du boss :
  "ca dit quoi l'equipe ? Alors tu es arrive au stade final de ce projet pokemon.
   C'est bien ouais. Par contre je te previens si tu perds ca part sur un 0 etoile
   sur le projet. Dans ce cas, je vais te montrer ce qu'est du machine learning !"

BOSS_EQUIPE_CONFIG (6 Pokémon fixes, niveau 85)
  1. Métalosse Shiny  - Steel/Psychic  - Nature Brave    - Attaquant Physique
  2. Drattak          - Dragon/Flying  - Nature Rigide   - Attaquant Physique
  3. Trioxyde         - Fire/Flying    - Nature Modeste  - Attaquant Spécial
  4. Kyogre           - Water          - Nature Modeste  - Attaquant Spécial
  5. Groudon          - Ground         - Nature Brave    - Attaquant Physique
  6. Gardevoir Shiny  - Psychic/Fairy  - Nature Modeste  - Attaquant Spécial

CLASS : BossIA
  soins_restants = 3 (plus que les dresseurs normaux)
  seuil_soin     = 0.40 (soin si < 40% PV)
  nom/titre      = "Boss Champion"

  Équipe :
    _calculer_stats(stats_base, nature) → dict
      Formule identique à DresseurIA mais avec NIVEAU_BOSS = 85 fixe.

    _choisir_attaques(types, role) → list
      Sélection ultra-stratégique : STAB triées par puissance décroissante,
      couverture ≥ 80, statuts débilitants, 4 slots maximum.

  IA avancée (supérieure au dresseur normal) :
    choisir_action(ennemi_joueur) → dict
      1. Évaluer si un switch stratégique est avantageux
      2. Si PV < 40% et soins disponibles → soigne
      3. Sinon → meilleure attaque

    _evaluer_switch(ennemi) → Pokemon | None
      Calcule _score_matchup() pour chaque Pokémon en réserve vivant.
      Switch seulement si un Pokémon ferait 50% mieux (score * 1.5) que l'actif.

    _score_matchup(attaquant, defenseur) → float
      max(puissance * mult_type * STAB pour chaque move) / résistance_ennemi
      Bonus si nos types résistent aux types ennemis.

    effectuer_switch(nouveau_pk) → str
      Change pokemon_actif, retourne message de changement.

    utiliser_soin() → str
      Restaure 60% des HP max (plus puissant que les dresseurs normaux).

  Victoire boss :
    Après victoire → phrase de félicitation affichée en dialogue.
    "bravo c'est bien, gg, tu as fini ce jeu. voici ton ecran de victoire."


────────────────────────────────────────────────────────────────────────────────
  intro.py  (core/intro.py)
────────────────────────────────────────────────────────────────────────────────
Rôle : Séquence d'introduction complète (création de personnage).

Flux en 5 étapes :
  1. S_TALK_1  : Discours du professeur (texte défilant)
  2. S_GENDER  : Choix du sexe (Garçon / Fille) avec flèches
  3. S_NAME    : Saisie du nom (10 caractères max, clavier alphanumérique)
  4. S_STARTER : Choix du starter parmi 3 (Flamiaou / Grenousse / Arcko)
                 Chaque starter peut être shiny (taux 1/4096)
  5. S_TALK_2  : Dernier discours → sauvegarde + lancement du jeu

CLASS : IntroView (arcade.View)
  bgm / bgm_player : Charge et joue intro.mp3 au démarrage.
  Dans _finish() : arcade.stop_sound() avant de lancer PokeFantasyGame.
  Crée la sauvegarde slot_X.json avec les données du personnage.
  Écrit dresseur_config.json pour synchronisation inter-modules.


────────────────────────────────────────────────────────────────────────────────
  main.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Point d'entrée, menu principal avec sélection de slots.

CLASS : MainMenuView (arcade.View)
  États du menu :
    STATE_MAIN      : Menu principal (Nouvelle Partie / Continuer)
    STATE_NEW_SLOTS : Sélection du slot pour une nouvelle partie
    STATE_CONTINUE  : Sélection du slot pour continuer
    STATE_CONFIRM   : Confirmation écrasement d'une save existante

  get_save_slots() → list
    Lit les 3 fichiers saves/slot_X.json.
    Retourne une liste de 3 éléments : None (vide) ou dict (save existante).
    Affiche le nom du dresseur, le stage et l'heure de dernière sauvegarde.

  Navigation : flèches Haut/Bas, Entrée pour valider, Echap pour annuler.
  Animation de fond avec timer (pulsations, particules).


────────────────────────────────────────────────────────────────────────────────
  test.py  (core/test.py)  —  PokeFantasyGame
────────────────────────────────────────────────────────────────────────────────
Rôle : Boucle de jeu principale. Hérite de arcade.Window.

Constantes :
  TYPE_BACKGROUNDS : Mapping type Pokémon → fichier background
    Eau/Glace   → glace.png
    Psy/Électrik→ labo.jpg
    Normal/Fée  → prairie.jpg
    Sol/Feu/Roche/Acier → volcan.jpg
    Insecte/Plante → jungle.png
    Combat/Dragon/Vol → sommet.png
    Spectre/Ténèbres/Poison → manoir.png
  BG_DEFAUT  = "prairie.jpg"
  BG_ARENE   = "arene.jpg"  ← utilisé pour TOUS les combats dresseur et boss

BOUTIQUE_CATALOGUE (10 articles) :
  Poké Ball 200P, Great Ball 600P, Ultra Ball 1200P, Master Ball 9999P
  Potion 300P, Super Potion 700P, Hyper Potion 1500P, Max Potion 2500P
  Rappel 1500P, Max Rappel 4000P

ÉTATS DU JEU (machine à états) :
  INTER_STAGE         : Menu entre stages (COMBATTRE / BOUTIQUE / POKEDEX)
  BOUTIQUE            : Écran boutique
  POKEDEX             : Écran Pokédex (Pokémon capturés)
  DRESSEUR_DIALOGUE   : Dialogue pré-combat dresseur/boss
  DRESSEUR_GLISSEMENT : Animation glissement du dresseur
  VICTOIRE_BOSS_DIALOGUE : Dialogue post-victoire du boss
  VICTOIRE_BOSS       : Écran intermédiaire victoire
  ECRAN_FIN           : Écran final (wing.png + CONGRATULATIONS)
  CAPTURE_PLEIN       : Choix sacrifice quand équipe de 6 pleine
  PRINCIPAL           : Menu de combat (ATTAQUE / SAC / EQUIPE / FUITE)
  ATTAQUE             : Sélection de la capacité
  SAC                 : Sélection de l'objet
  EQUIPE              : Sélection du Pokémon (changement)
  CHOIX_SOIN          : Sélection du Pokémon cible pour un soin
  ANIM_BALL           : Animation de lancer de Poké Ball
  ANIM_EVO            : Animation d'évolution (clignotement)
  DEMANDE_EVO         : Confirmation avant évolution
  MESSAGE_J           : Message côté joueur, déclenche riposte
  MESSAGE_E           : Message côté ennemi
  MESSAGE_V           : Message victoire (attribuer XP puis vérifier évo)
  MESSAGE_STAGE       : Annonce passage de stage
  MESSAGE_FUITE       : Message fuite réussie
  GAME_OVER           : Écran game over

Méthodes principales :
  charger_donnees()
    Charge save_data, pokemon_data, capacite_list, evolution_config.
    Reconstruit l'équipe du joueur sous forme d'instances Pokemon.
    Charge les sprites existants.

  sauvegarder_donnees()
    Sérialise l'équipe (to_dict()), écrit dans saves/slot_X.json
    et dans dresseur_config.json.

  _niveau_range_pour_stage() → (int, int)
    Stage 1 → (2, 3). Stage 99 → (95, 96).
    Formule : 2 + (stage-1) * (95/98)

  generer_ennemi_aleatoire()
    Scanne SPRITE_PATH pour les *_face.png.
    Filtre par _seuil_evolution() pour cohérence niveau.
    Assigne le niveau dans la plage du stage.
    Met à jour _bg_actuel selon le premier type.

  demarrer_combat_dresseur()
    Crée un DresseurIA, passe en état DRESSEUR_DIALOGUE.
    L'ennemi n'est visible qu'après le glissement.

  demarrer_combat_boss()
    Crée un BossIA. Arrête la musique courante.
    Charge final.mp3. Met background arene.jpg.
    Passe en DRESSEUR_DIALOGUE.

  entrer_en_combat()
    Stage >= 100 → demarrer_combat_boss()
    DresseurIA.doit_apparaitre() (20%) → demarrer_combat_dresseur()
    Sinon → generer_ennemi_aleatoire() + état PRINCIPAL

  finaliser_capture()
    Si succès :
      - Enregistre au Pokédex (possede=True)
      - Équipe < 6 : ajoute directement + _avancer_stage_apres_capture()
      - Équipe = 6 : stocke dans _pokemon_capture_temp, état CAPTURE_PLEIN
    Si échec : message + retour à MESSAGE_J.

  _fin_combat_victoire()
    Boss vaincu → dialogue de victoire boss (VICTOIRE_BOSS_DIALOGUE)
    Dresseur vaincu → gain argent + stage + 1 + MESSAGE_STAGE
    Dresseur encore des Pokémon → changer_pokemon() + nouveau combat
    Sauvage vaincu → stage + 1

  _game_over_retour_menu()
    Arrête la musique.
    Supprime saves/slot_X.json et dresseur_config.json.
    Relance main.main() (retour menu principal propre).

  _get_background(type_principal) → texture | None
    Cherche le fichier via TYPE_BACKGROUNDS + cache.

  _get_background_fichier(filename) → texture | None
    Charge par nom de fichier direct (pour arene.jpg du boss).

  _draw_pokedex()
    Lit pokedex.json, filtre possede=True, pagine (12 par page, 3 colonnes).
    Affiche nom + ATK + DEF de chaque Pokémon capturé.
    Gauche/Droite pour changer de page, X pour retour.

  _draw_victoire_boss()
    Fond vert, "VICTOIRE !", "Tu as battu le Boss !". Espace → ECRAN_FIN.

  _draw_ecran_fin()
    Charge wing.png en plein écran. Affiche "CONGRATULATIONS !" en doré.
    Espace → ferme le jeu.


────────────────────────────────────────────────────────────────────────────────
  fetch_moves.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Script de fetch pour télécharger les capacités depuis PokéAPI.
       Génère data/capacite_list.json.
Utilise : requests, json, pathlib, time.
Peut être relancé pour mettre à jour la base de capacités.

────────────────────────────────────────────────────────────────────────────────
  sprite_download.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Téléchargement en masse des sprites Pokémon depuis PokéAPI.
       Crée la structure asset/sprite/ avec les 4 variantes par Pokémon.
Utilise : urllib.request, concurrent.futures (ThreadPoolExecutor),
          pathlib, json, time.
ThreadPoolExecutor : téléchargement parallèle pour accélérer le processus.

────────────────────────────────────────────────────────────────────────────────
  type_logo.py
────────────────────────────────────────────────────────────────────────────────
Rôle : Script de génération/téléchargement des icônes de types.
       Crée les fichiers PNG dans asset/types/.


================================================================================
  6. FLUX DE JEU COMPLET
================================================================================

DÉMARRAGE
  main.py → MainMenuView
    ├── Nouvelle Partie → Sélection slot → IntroView
    │     ├── Discours prof + choix sexe/nom/starter
    │     ├── intro.mp3 joue pendant tout l'intro
    │     ├── Sauvegarde créée (slot_X.json + dresseur_config.json)
    │     └── arcade.stop_sound(intro) → PokeFantasyGame (battle_theme.mp3)
    └── Continuer → Sélection slot → PokeFantasyGame (battle_theme.mp3)

BOUCLE DE JEU (PokeFantasyGame)
  INTER_STAGE
    ├── COMBATTRE → entrer_en_combat()
    │     ├── Stage >= 100 → BossIA → DRESSEUR_DIALOGUE → (glissement) → PRINCIPAL
    │     ├── 20% chance → DresseurIA → DRESSEUR_DIALOGUE → (glissement) → PRINCIPAL
    │     └── 80% chance → Pokémon sauvage → PRINCIPAL
    ├── BOUTIQUE → Achat d'objets avec PokéDollars
    └── POKEDEX  → Consultation des Pokémon capturés

COMBAT (états MESSAGE_J / MESSAGE_E / PRINCIPAL / ATTAQUE / SAC / EQUIPE)
  Tour du joueur → TurnManager.executer_attaque() → MESSAGE_J
  MESSAGE_J :
    - Ennemi KO → attribuer_xp() → MonnaieEngine.calculer_gain() → MESSAGE_V
    - Ennemi vivant :
        Boss   → choisir_action() : switch stratégique / soin / attaque
        Dresseur → choisir_action() : soin / attaque optimale
        Sauvage  → random.choice(moves_obj)
      → MESSAGE_E
  MESSAGE_E :
    - Joueur KO + équipe KO → GAME_OVER (save supprimée → menu)
    - Joueur KO + équipe vivante → EQUIPE (changer obligatoire)
    - Sinon → PRINCIPAL

CAPTURE
  Lancer ball → ANIM_BALL → CaptureEngine.tenter_capture()
  Succès + équipe < 6 → ajout équipe + stage +1 → MESSAGE_STAGE
  Succès + équipe = 6 → CAPTURE_PLEIN :
    - Entrée → remplacer un Pokémon sacrifié → stage +1
    - X     → libérer le capturé (gardé dans Pokédex) → stage +1

ÉVOLUTION
  MESSAGE_V → verifier_evolution() → DEMANDE_EVO → ANIM_EVO → finaliser_evolution()
  Recalcul stats via LevelEngine. Mise à jour Pokédex.

BOSS (stage 100)
  final.mp3 + arene.jpg + BossIA (6 Pokémon niv 85)
  IA switch stratégique (50% meilleur = switch)
  3 guérisons à 60% PV max
  Victoire → VICTOIRE_BOSS_DIALOGUE → VICTOIRE_BOSS → ECRAN_FIN (wing.png)
  Défaite  → GAME_OVER → save supprimée → retour menu


================================================================================
  7. SYSTÈMES DE JEU
================================================================================

SYSTÈME DE STAGES
  Progression linéaire 1 → 99 (sauvage/dresseur) + 100 (boss)
  Niveau des ennemis : base = 2 + (stage-1) * (95/98)
  Stage 1 → niv 2-3    Stage 50 → niv ~50    Stage 99 → niv 95-96
  Pokémon filtrés par seuil d'évolution : impossible d'affronter une forme
  finale trop tôt (ex: Mammochon niv 33 minimum via évolution).

SYSTÈME MONÉTAIRE
  Gain combat sauvage : 15P × niveau × mult_stage × variation
  Gain combat dresseur : ×2.5 + somme des 3 Pokémon de l'équipe
  Affichage en bas à droite pendant le combat et sur l'écran inter-stage.

SYSTÈME DE SAUVEGARDE
  3 slots indépendants (saves/slot_1.json à slot_3.json).
  Auto-sauvegarde après chaque combat, achat, évolution, capture.
  Format JSON avec : équipe complète, inventaire, argent, stage, nom.
  GAME_OVER : supprime la save du slot actif (permadeath).

TAUX SHINY
  1/4096 (même taux que les jeux officiels gen 6+).
  Appliqué lors du choix du starter dans l'intro et sur les ennemis.
  Un Pokémon shiny utilise les sprites *_shiny_*.

SYSTÈME D'ÉQUIPE (6 max)
  Le joueur peut avoir jusqu'à 6 Pokémon simultanément.
  À 6 Pokémon + capture réussie → menu CAPTURE_PLEIN pour choisir le sacrifice.
  Le Pokémon sacrifié est libéré. Celui qui est capturé le remplace.
  Dans les deux cas (gardé ou libéré), possede=True dans le Pokédex.

BACKGROUNDS DYNAMIQUES
  Changent selon le premier type du Pokémon ennemi (sauvage uniquement).
  Les combats dresseur et boss utilisent toujours arene.jpg.
  Cache en mémoire pour éviter les rechargements répétitifs.

DRESSEUR IA
  Apparition : 20% par stage (DresseurIA.doit_apparaitre()).
  Équipe de 3 Pokémon avec nature et attaques stratégiques.
  Dialogue aléatoire parmi 3 phrases cultes, animation glissement vers la droite.
  Image aléatoire parmi 5 variantes (dresseur.png à dresseur_5.png).
  2 soins intelligents (utilisés si PV < 35%).

BOSS IA
  Uniquement au stage 100. Équipe fixe de 6 légendaires niveau 85.
  IA avancée avec switch stratégique (analyse type + puissance + résistance).
  3 soins à 60% PV max. Musique et background dédiés.
  Victoire → écran de félicitations + image wing.png.


================================================================================
  8. DONNÉES JSON
================================================================================

saves/slot_X.json — Structure :
  {
    "slot_num":      1,
    "nom_dresseur":  "Sacha",
    "sexe":          "garcon",
    "stage":         15,
    "argent":        2400,
    "equipe": [
      {
        "nom":        "Flamiaou",
        "niveau":     18,
        "nature":     "Brave",
        "hp_base":    65,
        "hp_actuel":  48,
        "xp":         420,
        "types":      ["Feu"],
        "stats":      {"attaque": 32, "defense": 26, "vitesse": 28,
                       "attaque_spe": 34, "defense_spe": 30},
        "capacites":  ["Griffe", "Flammèche", "Rugissement", "Danse Lames"],
        "statut":     null,
        "stages":     {"attaque": 0, "defense": 0, "vitesse": 0,
                       "attaque_spe": 0, "defense_spe": 0},
        "compteur_toxic": 0
      }
    ],
    "inventaire": [
      {"nom": "ultra-ball", "qty": 3, "cat": "balls"}
    ]
  }

data/pokedex.json — Structure :
  {
    "pokemon_rencontres": [
      {
        "nom":         "Flamiaou",
        "hp_base":     55,
        "attaque":     18,
        "defense":     14,
        "vu":          true,
        "possede":     true,
        "description": "Capturé par le joueur."
      }
    ]
  }


================================================================================
  9. RÉSUMÉ DES FONCTIONNALITÉS
================================================================================

  [x] Menu principal avec 3 slots de sauvegarde
  [x] Séquence d'introduction complète (sexe, nom, starter)
  [x] Musique intro.mp3 pendant l'intro, battle_theme.mp3 en jeu
  [x] Combat Pokémon au tour par tour (attaque, sac, équipe, fuite)
  [x] 18 types avec table de multiplicateurs complète (gen 6+, Fée inclus)
  [x] 24 natures avec effets sur les stats (+10%/-10%)
  [x] Coups critiques (6.25%), précision, STAB, variation aléatoire
  [x] Statuts : Brûlure, Paralysie, Poison, Toxique, Sommeil, Gelé
  [x] Effets de fin de tour (dégâts de statut progressifs)
  [x] Système d'expérience et montée de niveau avec recalcul des stats
  [x] Apprentissage de nouvelles capacités par niveau (learnset)
  [x] Évolutions par niveau avec animation de clignotement
  [x] Système de capture avec formule multicritères (ball, PV, statut, niveau)
  [x] Gestion équipe pleine (6 max) avec choix sacrifice ou libération
  [x] Système de stages 1-99 avec niveaux ennemis cohérents
  [x] Filtrage des Pokémon par stade d'évolution (cohérence niveau)
  [x] Backgrounds dynamiques selon le type du Pokémon ennemi (7 ambiances)
  [x] Pokédex avec filtrage capturés, pagination, ATK/DEF affichés
  [x] Boutique inter-stage (10 articles, gestion stock, PokéDollars)
  [x] Système monétaire complet (gain sauvage/dresseur, scalé par stage)
  [x] Dresseur IA (20% chance, équipe 3 Pokémon, IA attaque + soin)
  [x] Dialogue dresseur avec 3 phrases cultes + animation glissement
  [x] Image dresseur aléatoire parmi 5 variantes
  [x] Boss final stage 100 : équipe 6 légendaires niv 85 (dont 2 shinies)
  [x] IA boss avec switch stratégique, 3 soins, évaluation de matchup
  [x] Musique finale (final.mp3) et background arène pour boss
  [x] Phrase du boss sur les enjeux du projet et le machine learning
  [x] Victoire boss : dialogue, écran victoire, wing.png + CONGRATULATIONS
  [x] GAME_OVER : suppression de la save + retour menu (permadeath)
  [x] Taux shiny 1/4096 sur les starters et les Pokémon sauvages
  [x] Badge de stage affiché en haut à gauche pendant les combats
  [x] Indicateur argent en bas à droite
  [x] Overlay de boost (touche V) pour voir les stages de combat
  [x] Navigation clavier complète (flèches, Entrée, Espace, X, Echap)
  [x] Auto-sauvegarde après chaque action importante
  [x] Téléchargement automatique des sprites et capacités via PokéAPI

================================================================================
                           FIN DU README
================================================================================
