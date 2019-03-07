"""The MoveDex."""

import typing

import attr

from pokemaster._database import get_move
from pokemaster.pokemon import Pokemon


@attr.s(auto_attribs=True, kw_only=True)
class Move:
    """The base class for all moves."""

    id: int
    identifier: str
    name: str
    generation: int
    type: str
    power: int
    max_pp: int
    accuracy: typing.Optional[int]
    priority: int
    target: str
    damage_class: str
    effect_id: int
    description: str
    short_description: str
    effect_chance: int
    machines: typing.List[int]
    category: str
    ailment: str
    min_hits: int
    max_hits: int
    min_turns: int
    max_turns: int
    drain: int
    healing: int
    critical_rate: int
    ailment_chance: int
    flinch_chance: int
    stat_chance: int
    flags: int
    stat_changes: typing.List[typing.Tuple[str, int]]

    pp: int = None

    def __attrs_post_init__(self):
        self.pp = self.pp or self.max_pp

    @classmethod
    def from_veekun(cls, name: str, generation: int = 3) -> "Move":
        """Construct a ``Move`` instance from veekun's pokedex."""
        move_data = get_move(move=name, generation=generation)
        return cls(
            id=move_data.id,
            identifier=move_data.identifier,
            name=move_data.name,
            generation=move_data.generation_id,
            type=move_data.type.identifierSsSS,
            power=move_data.power,
            max_pp=move_data.pp,
            pp=move_data.pp,
            accuracy=move_data.accuracy,
            priority=move_data.priority,
            target=move_data.target.identifier,
            damage_class=move_data.damage_class.identifier,
            effect_id=move_data.move_effect.id,
            description=move_data.move_effect.effect,
            short_description=move_data.move_effect.short_effect,
            effect_chance=move_data.effect_chance,
            machines=[lambda x: x.id for x in move_data.machines],
            category=move_data.meta.category.identifier,
            ailment=move_data.meta.ailment.identifier,
            min_hits=move_data.meta.min_hits,
            max_hits=move_data.meta.max_hits,
            min_turns=move_data.meta.min_turns,
            max_turns=move_data.meta.max_turns,
            drain=move_data.meta.drain,
            healing=move_data.meta.healing,
            critical_rate=move_data.meta.crit_rate,
            ailment_chance=move_data.meta.ailment_chance,
            flinch_chance=move_data.meta.flinch_chance,
            stat_chance=move_data.meta.stat_chance,
            flags=move_data.flags,
            stat_changes=move_data.meta_stat_changes,
        )


@attr.s
class LaserFocus(Move):

    duration = attr.ib(default=2, kw_only=True)

    def start(self):
        """Activate the effect."""
        self.duration = 2

    def modify_critical_rate(
        self, critical_rate: float, source: Pokemon
    ) -> float:
        """Modify the critical rate."""
        if 'laser-focus' in source.semivulnerable_status:
            return float('inf')

    def end(self):
        """Reset the duration."""
        self.duration -= 1
