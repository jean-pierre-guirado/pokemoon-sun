class PokemonType:
    # Tableau des efficacités : [Attaquant][Défenseur]
    # 1.0 = Normal, 2.0 = Super Efficace, 0.5 = Pas très efficace, 0.0 = Immunité
    CHART = {
        "Normal": {"Roche": 0.5, "Spectre": 0.0, "Acier": 0.5},
        "Feu": {"Feu": 0.5, "Eau": 0.5, "Plante": 2.0, "Glace": 2.0, "Insecte": 2.0, "Roche": 0.5, "Dragon": 0.5, "Acier": 2.0},
        "Eau": {"Feu": 2.0, "Eau": 0.5, "Plante": 0.5, "Sol": 2.0, "Roche": 2.0, "Dragon": 0.5},
        "Plante": {"Feu": 0.5, "Eau": 2.0, "Plante": 0.5, "Poison": 0.5, "Sol": 2.0, "Vol": 0.5, "Insecte": 0.5, "Roche": 2.0, "Dragon": 0.5, "Acier": 0.5},
        "Électrik": {"Eau": 2.0, "Plante": 0.5, "Électrik": 0.5, "Sol": 0.0, "Vol": 2.0, "Dragon": 0.5},
        "Glace": {"Feu": 0.5, "Eau": 0.5, "Plante": 2.0, "Glace": 0.5, "Sol": 2.0, "Vol": 2.0, "Dragon": 2.0, "Acier": 0.5},
        "Combat": {"Normal": 2.0, "Glace": 2.0, "Poison": 0.5, "Vol": 0.5, "Psy": 0.5, "Insecte": 0.5, "Roche": 2.0, "Spectre": 0.0, "Ténèbres": 2.0, "Acier": 2.0, "Fée": 0.5},
        "Poison": {"Plante": 2.0, "Poison": 0.5, "Sol": 0.5, "Roche": 0.5, "Spectre": 0.5, "Acier": 0.0, "Fée": 2.0},
        "Sol": {"Feu": 2.0, "Plante": 0.5, "Électrik": 2.0, "Poison": 2.0, "Vol": 0.0, "Insecte": 0.5, "Roche": 2.0, "Acier": 2.0},
        "Vol": {"Plante": 2.0, "Électrik": 0.5, "Combat": 2.0, "Insecte": 2.0, "Roche": 0.5, "Acier": 0.5},
        "Psy": {"Combat": 2.0, "Poison": 2.0, "Psy": 0.5, "Ténèbres": 0.0, "Acier": 0.5},
        "Insecte": {"Feu": 0.5, "Plante": 2.0, "Combat": 0.5, "Poison": 0.5, "Vol": 0.5, "Psy": 2.0, "Spectre": 0.5, "Ténèbres": 2.0, "Acier": 0.5, "Fée": 0.5},
        "Roche": {"Feu": 2.0, "Glace": 2.0, "Combat": 0.5, "Sol": 0.5, "Vol": 2.0, "Insecte": 2.0, "Acier": 0.5},
        "Spectre": {"Normal": 0.0, "Psy": 2.0, "Spectre": 2.0, "Ténèbres": 0.5},
        "Dragon": {"Dragon": 2.0, "Acier": 0.5, "Fée": 0.0},
        "Ténèbres": {"Combat": 0.5, "Psy": 2.0, "Spectre": 2.0, "Ténèbres": 0.5, "Fée": 0.5},
        "Acier": {"Feu": 0.5, "Eau": 0.5, "Électrik": 0.5, "Glace": 2.0, "Roche": 2.0, "Acier": 0.5, "Fée": 2.0},
        "Fée": {"Feu": 0.5, "Combat": 2.0, "Poison": 0.5, "Dragon": 2.0, "Ténèbres": 2.0, "Acier": 0.5}
    }

    @staticmethod
    def get_multiplier(type_attaquant, type_defenseur):
        """Renvoie le multiplicateur de dégâts."""
        # Si le type défenseur n'est pas dans les faiblesses répertoriées, le dégât est neutre (1.0)
        return PokemonType.CHART.get(type_attaquant, {}).get(type_defenseur, 1.0)

# Exemple de test rapide :
# print(PokemonType.get_multiplier("Eau", "Feu")) # Devrait afficher 2.0