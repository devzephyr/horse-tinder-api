"""Seed the database with famous horses for demo purposes.

Usage:
    python -m app.db.seed

Requires a running PostgreSQL instance and completed migrations.
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.models.horse import Horse
from app.models.user import User

# Seed users who "own" the horses
SEED_USERS = [
    {
        "email": "bojack@horsetinder.com",
        "password": "SeedPass123!",
        "display_name": "BoJack Owner",
    },
    {
        "email": "racing@horsetinder.com",
        "password": "SeedPass123!",
        "display_name": "Racing Stable",
    },
    {
        "email": "historical@horsetinder.com",
        "password": "SeedPass123!",
        "display_name": "Historical Society",
    },
]

# BoJack Horseman characters
BOJACK_HORSES = [
    {
        "name": "BoJack Horseman",
        "breed": "Thoroughbred",
        "age": 18,
        "temperament": "moody",
        "bio": (
            "Washed-up 90s sitcom star. Star of Horsin' Around and Secretariat biopic. "
            "Looking for someone who appreciates self-destructive charm and rooftop pools."
        ),
        "location_city": "Hollywood",
        "location_state": "California",
        "location_country": "United States",
    },
    {
        "name": "Hollyhock Manheim-Mannheim-Guerrero-Robinson-Zilberschlag-Hsung-Fonzerelli-McQuack",
        "breed": "Draft Cross",
        "age": 6,
        "temperament": "gentle",
        "bio": (
            "College student at Wesleyan. Has eight dads. "
            "Enjoys long walks and figuring out who she really is."
        ),
        "location_city": "Middletown",
        "location_state": "Connecticut",
        "location_country": "United States",
    },
    {
        "name": "Beatrice Horseman",
        "breed": "Thoroughbred",
        "age": 25,
        "temperament": "spirited",
        "bio": (
            "Former debutante from the Sugarman family. "
            "Believes in tough love and the importance of appearances."
        ),
        "location_city": "San Francisco",
        "location_state": "California",
        "location_country": "United States",
    },
    {
        "name": "Butterscotch Horseman",
        "breed": "Mustang",
        "age": 26,
        "temperament": "stubborn",
        "bio": (
            "Failed novelist from the Midwest. Believes he's meant for greatness. "
            "Working on a novel about the American condition."
        ),
        "location_city": "Kansas City",
        "location_state": "Missouri",
        "location_country": "United States",
    },
    {
        "name": "Honey Sugarman",
        "breed": "Arabian",
        "age": 12,
        "temperament": "calm",
        "bio": (
            "A socialite from the 1940s. Loves dancing and her children more than anything. "
            "Time has not been kind."
        ),
        "location_city": "Traverse City",
        "location_state": "Michigan",
        "location_country": "United States",
    },
]

# Second batch of BoJack horses (separate owner due to 5-horse-per-user limit)
BOJACK_HORSES_2 = [
    {
        "name": "Crackerjack Sugarman",
        "breed": "Quarter Horse",
        "age": 5,
        "temperament": "spirited",
        "bio": (
            "A brave young stallion who signed up for the war. "
            "The best of the Sugarman family."
        ),
        "location_city": "Traverse City",
        "location_state": "Michigan",
        "location_country": "United States",
    },
    {
        "name": "Secretariat (BoJack)",
        "breed": "Thoroughbred",
        "age": 10,
        "temperament": "spirited",
        "bio": (
            "The greatest racehorse who ever lived -- until he wasn't. "
            "When you get to the top of the mountain, keep running."
        ),
        "location_city": "Louisville",
        "location_state": "Kentucky",
        "location_country": "United States",
    },
    {
        "name": "Joseph Sugarman",
        "breed": "Standardbred",
        "age": 28,
        "temperament": "stubborn",
        "bio": (
            "Wealthy sugar magnate. Believes in discipline and decorum. "
            "Emotions are for the weak."
        ),
        "location_city": "Traverse City",
        "location_state": "Michigan",
        "location_country": "United States",
    },
]

# Real-world famous horses
FAMOUS_HORSES = [
    {
        "name": "Secretariat",
        "breed": "Thoroughbred",
        "age": 5,
        "temperament": "spirited",
        "bio": (
            "1973 Triple Crown winner. Set records at the Kentucky Derby, Preakness, "
            "and Belmont Stakes that still stand. 31 lengths at Belmont. "
            "Widely considered the greatest racehorse of all time."
        ),
        "location_city": "Paris",
        "location_state": "Kentucky",
        "location_country": "United States",
    },
    {
        "name": "Seabiscuit",
        "breed": "Thoroughbred",
        "age": 7,
        "temperament": "stubborn",
        "bio": (
            "Undersized and overlooked, became a symbol of hope during the Great Depression. "
            "Beat War Admiral in the 1938 Match of the Century. "
            "Proof that heart matters more than pedigree."
        ),
        "location_city": "Willits",
        "location_state": "California",
        "location_country": "United States",
    },
    {
        "name": "Man o' War",
        "breed": "Thoroughbred",
        "age": 4,
        "temperament": "spirited",
        "bio": (
            "Won 20 of 21 career races. Dominated the 1920s racing scene. "
            "Sire of War Admiral and grandfather of Seabiscuit. "
            "A true dynasty founder."
        ),
        "location_city": "Lexington",
        "location_state": "Kentucky",
        "location_country": "United States",
    },
    {
        "name": "War Admiral",
        "breed": "Thoroughbred",
        "age": 5,
        "temperament": "spirited",
        "bio": (
            "1937 Triple Crown winner and son of Man o' War. "
            "Small but fierce -- only 15.2 hands. Lost the famous Match of the Century "
            "to Seabiscuit but remains one of the all-time greats."
        ),
        "location_city": "Lexington",
        "location_state": "Kentucky",
        "location_country": "United States",
    },
    {
        "name": "Black Beauty",
        "breed": "Friesian",
        "age": 8,
        "temperament": "gentle",
        "bio": (
            "A handsome horse with a star on the forehead and one white foot. "
            "Has seen the best and worst of humanity. Believes in kindness and patience. "
            "Inspired generations to treat horses with dignity."
        ),
        "location_city": "Norfolk",
        "location_state": None,
        "location_country": "United Kingdom",
    },
    {
        "name": "Comanche",
        "breed": "Mustang",
        "age": 12,
        "temperament": "calm",
        "bio": (
            "Sole survivor of the US 7th Cavalry at the Battle of the Little Bighorn (1876). "
            "Wounded seven times throughout his career. "
            "Retired with full military honors."
        ),
        "location_city": "Fort Riley",
        "location_state": "Kansas",
        "location_country": "United States",
    },
    {
        "name": "Bucephalus",
        "breed": "Thessalian",
        "age": 10,
        "temperament": "spirited",
        "bio": (
            "War horse of Alexander the Great. Tamed at age 12 by Alexander himself "
            "when no one else could. Carried him from Greece to India. "
            "A city was named in his honor."
        ),
        "location_city": "Jhelum",
        "location_state": "Punjab",
        "location_country": "Pakistan",
    },
    {
        "name": "Marengo",
        "breed": "Arabian",
        "age": 14,
        "temperament": "calm",
        "bio": (
            "Napoleon Bonaparte's most famous war horse. "
            "Carried Napoleon through Austerlitz, Jena, and Waterloo. "
            "Wounded eight times in battle. Small but unshakeable under fire."
        ),
        "location_city": "Paris",
        "location_state": None,
        "location_country": "France",
    },
    {
        "name": "Copenhagen",
        "breed": "Thoroughbred",
        "age": 15,
        "temperament": "spirited",
        "bio": (
            "The Duke of Wellington's charger at the Battle of Waterloo. "
            "Carried Wellington for 17 hours straight during the battle. "
            "Retired to a life of leisure on the estate grounds."
        ),
        "location_city": "Stratfield Saye",
        "location_state": "Hampshire",
        "location_country": "United Kingdom",
    },
    {
        "name": "Phar Lap",
        "breed": "Thoroughbred",
        "age": 5,
        "temperament": "gentle",
        "bio": (
            "New Zealand-born, Australian racing legend of the early 1930s. "
            "Won 37 of 51 starts including the Melbourne Cup. "
            "A beloved national hero whose mysterious death still sparks debate."
        ),
        "location_city": "Melbourne",
        "location_state": "Victoria",
        "location_country": "Australia",
    },
]


async def seed_database() -> None:
    """Populate the database with seed users and famous horses."""
    async with async_session_factory() as db:
        # Check if seed data already exists
        from sqlalchemy import select

        existing = await db.execute(
            select(User).where(User.email == "bojack@horsetinder.com")
        )
        if existing.scalar_one_or_none():
            print("Seed data already exists. Skipping.")
            return

        hashed = hash_password("SeedPass123!")
        users = []
        for user_data in SEED_USERS:
            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                hashed_password=hashed,
                display_name=user_data["display_name"],
                role="user",
            )
            db.add(user)
            users.append(user)

        await db.flush()

        # BoJack characters -- split across two users (max 5 per user)
        bojack_owner = users[0]
        for horse_data in BOJACK_HORSES:
            db.add(Horse(id=uuid.uuid4(), owner_id=bojack_owner.id, **horse_data))

        racing_owner = users[1]
        for horse_data in BOJACK_HORSES_2:
            db.add(Horse(id=uuid.uuid4(), owner_id=racing_owner.id, **horse_data))

        # Real-world famous horses -- split across two users (max 5 per user)
        historical_owner = users[2]
        for horse_data in FAMOUS_HORSES[:5]:
            db.add(Horse(id=uuid.uuid4(), owner_id=historical_owner.id, **horse_data))

        # Create a 4th user for the remaining famous horses
        extra_owner = User(
            id=uuid.uuid4(),
            email="legends@horsetinder.com",
            hashed_password=hashed,
            display_name="Legends Stable",
            role="user",
        )
        db.add(extra_owner)
        await db.flush()

        for horse_data in FAMOUS_HORSES[5:]:
            db.add(Horse(id=uuid.uuid4(), owner_id=extra_owner.id, **horse_data))

        await db.commit()
        print(f"Seeded {len(BOJACK_HORSES) + len(BOJACK_HORSES_2) + len(FAMOUS_HORSES)} horses across 4 users.")


if __name__ == "__main__":
    asyncio.run(seed_database())
