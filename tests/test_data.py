from grok_rpg.data_load import catalog, validate_catalog
from grok_rpg.manifest import default_jobs


def test_catalog_cross_refs() -> None:
    errors = validate_catalog(catalog())
    assert errors == []


def test_ability_ids_stable() -> None:
    abs_ = catalog()["abilities"]
    expected = {
        "fighter.slash",
        "fighter.cleave",
        "fighter.shield_bash",
        "fighter.leap",
        "mage.fireball",
        "mage.ice_nova",
        "mage.lightning",
        "mage.blink",
        "cleric.smite",
        "cleric.heal",
        "cleric.ward",
        "cleric.consecrate",
    }
    assert expected <= set(abs_)


def test_manifest_has_class_vfx() -> None:
    ids = {j["id"] for j in default_jobs()}
    for needed in (
        "char.fighter.idle",
        "char.mage.idle",
        "char.cleric.idle",
        "vfx.slash",
        "vfx.fireball",
        "vfx.holy_bless",
        "mon.undead_ghost.idle",
        "item.ghost_ectoplasm",
    ):
        assert needed in ids
