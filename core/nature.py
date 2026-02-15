class NatureEngine: # On renomme pour correspondre aux imports du moteur
    # On met les données en variable de classe (statique) pour y accéder facilement
    DATA = {
        "Assuré": ("Defense", "Attaque"),
        "Brave": ("Attaque", "Vitesse"),
        "Calme": ("Defense_Spe", "Attaque"),
        "Docile": (None, None),
        "Foufou": ("Attaque_Spe", "Defense_Spe"),
        "Gentil": ("Defense_Spe", "Defense"),
        "Hardi": (None, None),
        "Jovial": ("Vitesse", "Attaque_Spe"),
        "Lâche": ("Defense", "Defense_Spe"),
        "Malin": ("Defense", "Attaque_Spe"),
        "Malpoli": ("Defense_Spe", "Vitesse"),
        "Modeste": ("Attaque_Spe", "Attaque"),
        "Naïf": ("Vitesse", "Defense_Spe"),
        "Presse": ("Vitesse", "Defense"),
        "Prudent": ("Defense_Spe", "Attaque_Spe"),
        "Pudique": (None, None),
        "Relax": ("Defense", "Vitesse"),
        "Rigide": ("Attaque", "Attaque_Spe"),
        "Sérieux": (None, None),
        "Solo": ("Attaque", "Defense"),
        "Timide": ("Vitesse", "Attaque"),
        "Bizarre": (None, None),
        "Discret": ("Attaque_Spe", "Vitesse"),
        "Mauvais": ("Attaque", "Defense_Spe")
    }

    @staticmethod
    def get_multiplier(nature_name, stat_name):
        """Retourne le multiplicateur (1.1, 0.9 ou 1.0)."""
        if nature_name not in NatureEngine.DATA:
            return 1.0
        
        boost, nerf = NatureEngine.DATA[nature_name]
        
        # On normalise en minuscule pour éviter les erreurs de frappe
        s_name = stat_name.capitalize()
        if s_name == boost: return 1.1
        if s_name == nerf: return 0.9
        return 1.0

    @staticmethod
    def apply_nature_to_stats(nature_name, stats):
        """
        Applique la nature à un dictionnaire de stats complet.
        Utilisé par le CombatEngine.
        """
        new_stats = stats.copy()
        for s in new_stats:
            # On mappe les noms anglais/français si nécessaire
            mapping = {"attaque": "Attaque", "defense": "Defense", "vitesse": "Vitesse", 
                       "attaque_spe": "Attaque_Spe", "defense_spe": "Defense_Spe"}
            
            ref_name = mapping.get(s.lower(), s.capitalize())
            new_stats[s] = int(new_stats[s] * NatureEngine.get_multiplier(nature_name, ref_name))
        return new_stats