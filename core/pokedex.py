import json
import os

from core.config import POKEDEX_JSON
from core.utils import normaliser


class PokedexManager:
    """Gère la lecture, l'écriture et l'enregistrement des Pokémon dans le Pokédex."""

    @staticmethod
    def charger_pokedex() -> dict:
        if not os.path.exists(POKEDEX_JSON):
            return {"pokemon_rencontres": []}
        try:
            with open(POKEDEX_JSON, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    return {"pokemon_rencontres": content}
                if isinstance(content, dict) and "pokemon_rencontres" in content:
                    return content
                return {"pokemon_rencontres": []}
        except (json.JSONDecodeError, IOError):
            return {"pokemon_rencontres": []}

    @staticmethod
    def sauvegarder_pokedex(data: dict) -> None:
        with open(POKEDEX_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def enregistrer(pokemon, capture: bool = False) -> None:
        """Enregistre ou met à jour un Pokémon dans le Pokédex.

        Args:
            pokemon: Instance de Pokemon.
            capture: True si le Pokémon a été capturé par le joueur.
        """
        data    = PokedexManager.charger_pokedex()
        existant = next(
            (p for p in data["pokemon_rencontres"] if normaliser(p["nom"]) == normaliser(pokemon.nom)),
            None,
        )

        if not existant:
            nouveau = {
                "nom":        pokemon.nom,
                "hp_base":    pokemon.hp_base,
                "attaque":    pokemon.stats.get("attaque"),
                "defense":    pokemon.stats.get("defense"),
                "vu":         True,
                "possede":    capture,
                "description": "Capturé par le joueur." if capture else "Vu dans la nature.",
            }
            data["pokemon_rencontres"].append(nouveau)
        else:
            existant["vu"] = True
            if capture:
                existant["possede"]    = True
                existant["description"] = "Capturé par le joueur."

        PokedexManager.sauvegarder_pokedex(data)
