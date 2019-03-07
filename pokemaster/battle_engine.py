"""The engine that drives a battle.

How Turns Work
==============

1.  Before Turn

2.  Before Switch

[ Choose Command ]

3.  Switch
    *   Start Ability Effect
    *   Start Item Effect
    *   Mega Evolve

4.  Before Move (checks if move can start)

[ Sort Priorities ]

5.  Start Move Effect
    *   Try Hit
    *   Check Immunity
    *   Modify Base Power
    *   Calculate Damage
    *   Heal
    *   Apply Status Change
    *   Recoil
    *   Drain
    *   Reduce PP

6.  Faint

7.  Reduce Effect Duration

[ Choose Switch-ins for Fainted Pokémon ]
"""
import attr


@attr.s
class BattleController:
    """Govern all mechanisms for a battle."""

    ally_team = attr.ib()
    foe_team = attr.ib()
    terrain = attr.ib()
    weather = attr.ib()

    # single, double, or tripple
    battle_mode = attr.ib()
    rules = attr.ib()

    active_ally_pokemon = attr.ib()
    active_foe_pokemon = attr.ib()

    def start(self):
        """Start a turn."""
        effects = self.collect_effects()

        # run before turn
        for effect in effects:
            if effect.name == "before_turn":
                self.activate(effect)

    def collect_effects(self):
        """Collect all potential effects."""

    def activate(self, effect):
        """Activate a single effect."""
