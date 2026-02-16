import random

class CaptureEngine:
    @staticmethod
    def calculer_taux(ball_nom, ennemi):
        nom = ball_nom.lower().strip()
        
        # Multiplicateurs officiels (approximatifs)
        bonus_ball = 1.0
        if "master-ball" in nom: return 255 # Capture garantie
        elif "ultra-ball" in nom: bonus_ball = 2.0
        elif "great-ball" in nom: bonus_ball = 1.5
        elif "safari-ball" in nom: bonus_ball = 1.5
        
        # Formule de capture simplifiée
        # Plus les PV sont bas, plus la chance augmente
        ratio_hp = (3 * ennemi["max_hp"] - 2 * ennemi["hp"]) / (3 * ennemi["max_hp"])
        chance = ratio_hp * bonus_ball * 0.5 # 0.5 pour équilibrer la difficulté
        
        return chance

    @staticmethod
    def tenter_capture(ball_nom, ennemi):
        chance = CaptureEngine.calculer_taux(ball_nom, ennemi)
        if chance >= 1.0: return True
        return random.random() < chance