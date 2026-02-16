class ItemEngine:
    @staticmethod
    def utiliser_objet(item_nom, pokemon):
        nom = item_nom.lower().strip()
        soin = 0
        message = ""
        
        # --- LOGIQUE DE SOIN ---
        if "potion" in nom:
            if "max" in nom: soin = pokemon["max_hp"]
            elif "super" in nom: soin = 50
            elif "hyper" in nom: soin = 200
            else: soin = 20
            
            p_vieilles = pokemon["hp"]
            pokemon["hp"] = min(pokemon["max_hp"], pokemon["hp"] + soin)
            message = f"{pokemon['nom']} a récupéré {pokemon['hp'] - p_vieilles} PV !"
        
        elif "revive" in nom or "rappel" in nom:
            if pokemon["hp"] <= 0:
                pokemon["hp"] = pokemon["max_hp"] // 2 if "max" not in nom else pokemon["max_hp"]
                message = f"{pokemon['nom']} est de retour au combat !"
            else:
                message = "Cela n'aura aucun effet..."
        
        elif "full-restore" in nom:
            pokemon["hp"] = pokemon["max_hp"]
            message = f"Tous les PV de {pokemon['nom']} sont restaurés !"
            
        # --- LOGIQUE DU SUPER BONBON ---
        elif "rare-candy" in nom or "bonbon" in nom:
            # Si c'est un objet de classe Pokemon (Arcade)
            if hasattr(pokemon, 'gain_xp'):
                pokemon.gain_xp(pokemon.xp_max) 
                message = f"Incroyable ! {pokemon.nom} monte au niveau {pokemon.niveau} !"
            else:
                # Si c'est un dictionnaire (Pygame)
                pokemon["niveau"] += 1
                pokemon["max_hp"] += 5
                pokemon["hp"] = pokemon["max_hp"]
                message = f"{pokemon['nom']} monte au niveau {pokemon['niveau']} !"
            
        else:
            message = f"L'objet {item_nom} ne peut pas être utilisé ici."
            
        return message