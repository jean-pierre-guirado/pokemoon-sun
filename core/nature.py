class PokemonNature:
    def __init__(self):
        # Structure : { "Nom": (Stat Boostée, Stat Réduite) }
        # None signifie que la nature est neutre.
        self.natures_data = {
            "Assuré": ("Defense", "Attaque"),
            "Brave": ("Attaque", "Vitesse"),
            "Calme": ("Defense_Spe", "Attaque"),
            "Docile": (None, None),  # Neutre
            "Foufou": ("Attaque_Spe", "Defense_Spe"),
            "Gentil": ("Defense_Spe", "Defense"),
            "Hardi": (None, None),  # Neutre
            "Jovial": ("Vitesse", "Attaque_Spe"),
            "Lâche": ("Defense", "Defense_Spe"),
            "Malin": ("Defense", "Attaque_Spe"),
            "Malpoli": ("Defense_Spe", "Vitesse"),
            "Modeste": ("Attaque_Spe", "Attaque"),
            "Naïf": ("Vitesse", "Defense_Spe"),
            "Presse": ("Vitesse", "Defense"),
            "Prudent": ("Defense_Spe", "Attaque_Spe"),
            "Pudique": (None, None),  # Neutre
            "Relax": ("Defense", "Vitesse"),
            "Rigide": ("Attaque", "Attaque_Spe"),
            "Sérieux": (None, None),  # Neutre
            "Solo": ("Attaque", "Defense"),
            "Timide": ("Vitesse", "Attaque"),
            "Bizarre": (None, None),  # Neutre
            "Discret": ("Attaque_Spe", "Vitesse"),
            "Docile": (None, None),   # Neutre
            "Mauvais": ("Attaque", "Defense_Spe")
        }

    def get_multiplier(self, nature_name, stat_name):
        """
        Retourne le multiplicateur pour une stat donnée selon la nature.
        Ex: Rigide pour l'Attaque retournera 1.1
        """
        if nature_name not in self.natures_data:
            return 1.0
        
        boost, nerf = self.natures_data[nature_name]
        
        if stat_name == boost:
            return 1.1
        elif stat_name == nerf:
            return 0.9
        else:
            return 1.0

    def get_nature_info(self, nature_name):
        """Affiche les détails d'une nature"""
        if nature_name not in self.natures_data:
            return "Nature inconnue."
            
        boost, nerf = self.natures_data[nature_name]
        if boost is None:
            return f"Nature {nature_name} : Neutre (aucun bonus/malus)."
        else:
            return f"Nature {nature_name} : +10% {boost}, -10% {nerf}."

# --- EXEMPLE D'UTILISATION ---
if __name__ == "__main__":
    nature_manager = PokemonNature()
    
    # Test 1 : Nature Rigide
    print(nature_manager.get_nature_info("Rigide"))
    
    # Test 2 : Récupérer un multiplicateur précis
    multiplicateur = nature_manager.get_multiplier("Rigide", "Attaque")
    print(f"Multiplicateur Attaque pour 'Rigide' : x{multiplicateur}")
    
    # Test 3 : Nature neutre
    print(nature_manager.get_nature_info("Hardi"))