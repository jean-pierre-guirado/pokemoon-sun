class TypeChart:
    """Table des types Pokémon complète (Générations 6+)."""
    
    DATA = {
        "Normal": {
            "Roche": 0.5, "Spectre": 0.0, "Acier": 0.5
        },
        "Feu": {
            "Feu": 0.5, "Eau": 0.5, "Plante": 2.0, "Glace": 2.0, "Insecte": 2.0, "Roche": 0.5, "Dragon": 0.5, "Acier": 2.0
        },
        "Eau": {
            "Feu": 2.0, "Eau": 0.5, "Plante": 0.5, "Sol": 2.0, "Roche": 2.0, "Dragon": 0.5
        },
        "Plante": {
            "Feu": 0.5, "Eau": 2.0, "Plante": 0.5, "Poison": 0.5, "Sol": 2.0, "Vol": 0.5, "Insecte": 0.5, "Roche": 2.0, "Dragon": 0.5, "Acier": 0.5
        },
        "Électrik": {
            "Eau": 2.0, "Plante": 0.5, "Électrik": 0.5, "Sol": 0.0, "Vol": 2.0, "Dragon": 0.5
        },
        "Glace": {
            "Feu": 0.5, "Eau": 0.5, "Plante": 2.0, "Glace": 0.5, "Sol": 2.0, "Vol": 2.0, "Dragon": 2.0, "Acier": 0.5
        },
        "Combat": {
            "Normal": 2.0, "Glace": 2.0, "Poison": 0.5, "Vol": 0.5, "Psy": 0.5, "Insecte": 0.5, "Roche": 2.0, "Spectre": 0.0, "Ténèbres": 2.0, "Acier": 2.0, "Fée": 0.5
        },
        "Poison": {
            "Plante": 2.0, "Poison": 0.5, "Sol": 0.5, "Roche": 0.5, "Spectre": 0.5, "Acier": 0.0, "Fée": 2.0
        },
        "Sol": {
            "Feu": 2.0, "Électrik": 2.0, "Poison": 2.0, "Roche": 2.0, "Acier": 2.0, "Plante": 0.5, "Insecte": 0.5, "Vol": 0.0
        },
        "Vol": {
            "Plante": 2.0, "Électrik": 0.5, "Combat": 2.0, "Insecte": 2.0, "Roche": 0.5, "Acier": 0.5
        },
        "Psy": {
            "Combat": 2.0, "Poison": 2.0, "Psy": 0.5, "Ténèbres": 0.0, "Acier": 0.5
        },
        "Insecte": {
            "Feu": 0.5, "Plante": 2.0, "Combat": 0.5, "Poison": 0.5, "Vol": 0.5, "Psy": 2.0, "Spectre": 0.5, "Ténèbres": 2.0, "Acier": 0.5, "Fée": 0.5
        },
        "Roche": {
            "Feu": 2.0, "Glace": 2.0, "Combat": 0.5, "Sol": 0.5, "Vol": 2.0, "Insecte": 2.0, "Acier": 0.5
        },
        "Spectre": {
            "Normal": 0.0, "Psy": 2.0, "Spectre": 2.0, "Ténèbres": 0.5
        },
        "Dragon": {
            "Dragon": 2.0, "Acier": 0.5, "Fée": 0.0
        },
        "Ténèbres": {
            "Combat": 0.5, "Psy": 2.0, "Spectre": 2.0, "Ténèbres": 0.5, "Fée": 0.5
        },
        "Acier": {
            "Feu": 0.5, "Eau": 0.5, "Électrik": 0.5, "Glace": 2.0, "Roche": 2.0, "Acier": 0.5, "Fée": 2.0
        },
        "Fée": {
            "Feu": 0.5, "Combat": 2.0, "Poison": 0.5, "Dragon": 2.0, "Ténèbres": 2.0, "Acier": 0.5
        }
    }

    @classmethod
    def get_multiplier(cls, move_type: str, defender_types: list) -> float:
        """Calcule le multiplicateur total avec gestion des immunités."""
        multiplier = 1.0
        m_type = str(move_type).strip().capitalize()
        if m_type == "Electrik": m_type = "Électrik"

        for d_type in defender_types:
            d_type_clean = str(d_type).strip().capitalize()
            if d_type_clean == "Electrik": d_type_clean = "Électrik"
            
            # Récupère l'efficacité du type d'attaque sur le type du défenseur
            val = cls.DATA.get(m_type, {}).get(d_type_clean, 1.0)
            multiplier *= val
            
            # Si multiplicateur tombe à 0, on renvoie 0 immédiatement
            if multiplier == 0.0:
                return 0.0
        return multiplier

    @staticmethod
    def get_effectiveness_message(multiplier: float) -> str:
        """Texte de combat selon l'efficacité."""
        if multiplier >= 1.9: return "C'est super efficace !"
        if multiplier == 0.0: return "Ça n'affecte pas l'ennemi..."
        if 0.1 <= multiplier <= 0.6: return "Ce n'est pas très efficace..."
        return ""