from aiogram import Router

from . import admin, balance, bonus, dice, leaderboard, profile, referral, rules, start


def get_main_router() -> Router:
    """Assemble and return the root router with all feature routers included."""
    router = Router(name="main")

    # Order matters only where filters could overlap (e.g. admin commands
    # first so they are never shadowed by anything else).
    router.include_router(admin.router)
    router.include_router(start.router)
    router.include_router(profile.router)
    router.include_router(balance.router)
    router.include_router(bonus.router)
    router.include_router(rules.router)
    router.include_router(leaderboard.router)
    router.include_router(referral.router)
    router.include_router(dice.router)

    return router
