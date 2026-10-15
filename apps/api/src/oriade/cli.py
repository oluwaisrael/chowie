"""Explicit setup commands. Never seeds production automatically."""

import argparse
import getpass
from sqlalchemy import select
from oriade.shared.db import SessionLocal
from oriade.shared.models import User, Location, Category, Zone, MenuItem, Modifier, Inventory
from oriade.modules.identity.service import hasher


def seed():
    with SessionLocal() as db:
        if db.scalar(select(Location)):
            print("Catalog already exists; no data changed.")
            return
        location = Location(
            name="Óriade · Sample kitchen",
            address="Sample pickup location — confirm the real address with the restaurant",
        )
        db.add(location)
        db.flush()
        categories = {}
        for name, slug in [
            ("Rice & classics", "rice-classics"),
            ("Soups & swallows", "soups-swallows"),
            ("Sides & small chops", "sides"),
            ("Drinks", "drinks"),
        ]:
            c = Category(name=name, slug=slug)
            db.add(c)
            db.flush()
            categories[slug] = c.id
        for name, fee in [("Sample zone · nearby", 150000), ("Sample zone · extended", 250000)]:
            db.add(Zone(name=name, fee=fee, location_id=location.id))
        dishes = [
            (
                "Smoky jollof & chicken",
                "Long-grain jollof, flame-grilled chicken and golden, caramelized plantain.",
                650000,
                "rice-classics",
                "/images/jollof.webp",
                True,
            ),
            (
                "Egusi & pounded yam",
                "A rich melon-seed soup with leafy greens and tender beef, served with soft pounded yam.",
                700000,
                "soups-swallows",
                "/images/egusi.webp",
                True,
            ),
            (
                "Suya, the Óriade way",
                "Flame-kissed beef, warm yaji spice, fresh tomatoes and crisp red onion. Contains peanuts.",
                550000,
                "sides",
                "/images/suya.webp",
                True,
            ),
            (
                "Golden plantain",
                "Sweet ripe plantain, gently fried until golden at the edges.",
                180000,
                "sides",
                "",
                False,
            ),
            (
                "Puff-puff",
                "Six warm, golden bites. Soft in the middle, made for sharing.",
                200000,
                "sides",
                "",
                False,
            ),
            (
                "Hibiscus zobo",
                "A chilled hibiscus infusion with ginger and pineapple. 350 ml.",
                150000,
                "drinks",
                "",
                False,
            ),
        ]
        for name, description, price, category, image, featured in dishes:
            item = MenuItem(
                name=name,
                description=description,
                price=price,
                category_id=categories[category],
                location_id=location.id,
                image=image,
                featured=featured,
            )
            db.add(item)
            db.flush()
            db.add(Inventory(item_id=item.id))
            if category in {"rice-classics", "soups-swallows"}:
                db.add(Modifier(item_id=item.id, name="Extra grilled chicken", price=250000))
                db.add(Modifier(item_id=item.id, name="Extra plantain", price=100000))
        db.commit()
        print("Sample catalog created. No orders, customers, or performance data were fabricated.")


def admin(email):
    password = getpass.getpass("Admin password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email.lower())):
            raise SystemExit("User exists. Change access through an existing admin account.")
        db.add(
            User(
                email=email.lower(),
                name="Restaurant administrator",
                password_hash=hasher.hash(password),
                role="admin",
            )
        )
        db.commit()
        print("Administrator created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["seed", "create-admin"])
    parser.add_argument("--email")
    args = parser.parse_args()
    if args.command == "seed":
        seed()
    elif args.email:
        admin(args.email)
    else:
        parser.error("create-admin requires --email")
