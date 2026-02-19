import random

# NOTE: CombatEngine est importé ici pour usage dans TurnManager.
# L'import est effectué en haut du fichier pour éviter les imports circulaires.
# Si vous utilisez ce fichier seul, assurez-vous que core.engines est dans le path.
from core.engines import CombatEngine
from core.engines import StatusEngine


class TurnManager:
    """Gère l'ordre et l'exécution des tours de combat."""

    @staticmethod
    def determiner_ordre(p1, p2, move1, move2):
        """Détermine qui attaque en premier.
        
        Prend en compte la priorité des attaques, puis la vitesse.
        
        Returns:
            tuple: (premier_attaquant, second_attaquant)
        """
        prio1 = move1.get('priorite', 0) if move1 else 0
        prio2 = move2.get('priorite', 0) if move2 else 0

        if prio1 > prio2: return p1, p2
        if prio2 > prio1: return p2, p1

        v1 = CombatEngine._get_stat_actuelle(p1, "vitesse")
        v2 = CombatEngine._get_stat_actuelle(p2, "vitesse")

        # Paralysie réduit la vitesse de 50%
        if p1.statut == "Paralysie": v1 *= 0.5
        if p2.statut == "Paralysie": v2 *= 0.5

        if v1 > v2: return p1, p2
        if v2 > v1: return p2, p1

        # Égalité parfaite → hasard
        return random.choice([(p1, p2), (p2, p1)])

    @staticmethod
    def executer_attaque(attaquant, defenseur, move):
        """Gère une seule phase d'attaque : calcule les dégâts et applique les effets.
        
        Returns:
            str: Message de combat décrivant ce qui s'est passé.
        """
        if attaquant.hp <= 0:
            return f"{attaquant.nom} est KO et ne peut pas attaquer !"

        # Gestion de la paralysie (25% de chance de rater son tour)
        if attaquant.statut == "Paralysie" and random.random() < 0.25:
            return f"{attaquant.nom} est totalement paralysé !"

        # Gestion du sommeil
        if attaquant.statut == "Sommeil":
            return f"{attaquant.nom} est endormi !"

        # Gestion du gel (33% de chance de rester gelé)
        if attaquant.statut == "Gelé":
            if random.random() < 0.33:
                return f"{attaquant.nom} est gelé et ne peut pas bouger !"
            else:
                attaquant.statut = None  # Dégel automatique

        # Calcul des dégâts via CombatEngine
        dmg, mult, crit, miss, msg_effet = CombatEngine.calculer_degats(attaquant, defenseur, move)

        if miss:
            return f"{attaquant.nom} utilise {move['nom_attaque']} !\n{msg_effet}"

        defenseur.hp = max(0, defenseur.hp - dmg)

        # Construction du message
        lignes = [f"{attaquant.nom} utilise {move['nom_attaque']} !"]
        if dmg > 0:
            lignes.append(f"{defenseur.nom} perd {dmg} PV.")
        if msg_effet:
            lignes.append(msg_effet)

        return "\n".join(l for l in lignes if l)

    @staticmethod
    def executer_tour_complet(joueur, ennemi, move_joueur, move_ennemi):
        """Exécute un tour complet (les deux Pokémon attaquent + effets de fin de tour).
        
        Returns:
            str: Journal complet du tour.
        """
        premier, second = TurnManager.determiner_ordre(joueur, ennemi, move_joueur, move_ennemi)
        move_premier = move_joueur if premier is joueur else move_ennemi
        move_second  = move_ennemi if second is ennemi else move_joueur

        messages = []

        # Phase 1 : premier attaquant
        msg1 = TurnManager.executer_attaque(premier, second, move_premier)
        messages.append(msg1)

        # Phase 2 : second attaquant (seulement s'il est encore en vie)
        if second.hp > 0:
            msg2 = TurnManager.executer_attaque(second, premier, move_second)
            messages.append(msg2)

        # Phase 3 : effets de fin de tour (poison, brûlure, toxic)
        for p in [joueur, ennemi]:
            msg_eot = TurnManager.appliquer_effets_fin_de_tour(p)
            if msg_eot:
                messages.append(msg_eot)

        return "\n".join(messages)

    @staticmethod
    def appliquer_effets_fin_de_tour(pokemon):
        """Gère les dégâts de Poison, Brûlure et Toxique à la fin du tour.
        
        Returns:
            str: Message décrivant les dégâts subis, ou chaîne vide.
        """
        if pokemon.hp <= 0:
            return ""

        msg = ""
        if pokemon.statut == "Brûlure":
            degats = max(1, pokemon.hp_base // 16)
            pokemon.hp = max(0, pokemon.hp - degats)
            msg = f"La brûlure inflige {degats} dégâts à {pokemon.nom} !"

        elif pokemon.statut == "Poison":
            degats = max(1, pokemon.hp_base // 8)
            pokemon.hp = max(0, pokemon.hp - degats)
            msg = f"Le poison inflige {degats} dégâts à {pokemon.nom} !"

        elif pokemon.statut == "Toxique":
            pokemon.compteur_toxic = getattr(pokemon, 'compteur_toxic', 0) + 1
            degats = max(1, (pokemon.hp_base // 16) * pokemon.compteur_toxic)
            pokemon.hp = max(0, pokemon.hp - degats)
            msg = f"Le poison s'accentue ! {pokemon.nom} perd {degats} PV !"

        return msg
