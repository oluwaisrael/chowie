"""Explicit setup commands. Never seeds production automatically."""

import argparse
import getpass
from sqlalchemy import select
from oriade.shared.db import SessionLocal
from oriade.shared.models import User, Location, Category, Zone, MenuItem, Modifier, Inventory
from oriade.modules.identity.service import hasher


def seed():
    with SessionLocal() as db:
        location = db.scalar(select(Location).where(Location.name == "Óriade · Sample kitchen"))
        if not location and db.scalar(select(Location)):
            print("A non-sample catalog already exists; no demo data changed.")
            return
        if not location:
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
            ("Nigerian favourites", "nigerian-favourites"),
            ("International favourites", "international-favourites"),
            ("Breakfast & brunch", "breakfast-brunch"),
        ]:
            c = db.scalar(select(Category).where(Category.slug == slug))
            if not c:
                c = Category(name=name, slug=slug)
                db.add(c)
                db.flush()
            categories[slug] = c.id
        # The flat demo fee is intentionally illustrative; operators must confirm it.
        lgas = [
            "Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa",
            "Badagry", "Epe", "Eti-Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikeja",
            "Ikorodu", "Kosofe", "Lagos Island", "Lagos Mainland", "Mushin", "Ojo",
            "Oshodi-Isolo", "Shomolu", "Surulere",
        ]
        for legacy in db.scalars(select(Zone).where(
            Zone.location_id == location.id,
            Zone.name.in_(["Sample zone · nearby", "Sample zone · extended"]),
        )):
            legacy.active = False
        existing_zones = {z.name for z in db.scalars(select(Zone).where(Zone.location_id == location.id))}
        for lga in lgas:
            if lga not in existing_zones:
                db.add(Zone(name=lga, fee=200000, location_id=location.id))
        dishes = [
            (
                "Smoky jollof & chicken",
                "Long-grain jollof, flame-grilled chicken and golden, caramelized plantain.",
                650000,
                "rice-classics",
                "",
                True,
            ),
            (
                "Egusi & pounded yam",
                "A rich melon-seed soup with leafy greens and tender beef, served with soft pounded yam.",
                700000,
                "soups-swallows",
                "",
                True,
            ),
            (
                "Suya, the Óriade way",
                "Flame-kissed beef, warm yaji spice, fresh tomatoes and crisp red onion. Contains peanuts.",
                550000,
                "sides",
                "",
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
            ("Nigerian fried rice & chicken", "Colourful Nigerian fried rice with grilled chicken and sweet fried plantain.", 720000, "rice-classics", "", False),
            ("Amala, ewedu & gbegiri", "Soft amala with silky ewedu, hearty gbegiri and a slow-cooked beef portion.", 680000, "soups-swallows", "", False),
            ("Catfish pepper soup", "A warming pepper soup with catfish, aromatic spices and fresh scent leaf.", 750000, "soups-swallows", "", False),
            ("Ofada rice & ayamase", "Local Ofada rice with rich green pepper sauce and a boiled egg.", 650000, "nigerian-favourites", "", False),
            ("Coconut rice & grilled fish", "Fragrant coconut rice with a grilled fish portion and fresh herbs.", 850000, "rice-classics", "", False),
            ("Beans & ripe plantain", "Slow-cooked honey beans served with ripe golden plantain.", 480000, "nigerian-favourites", "", False),
            ("Moi moi", "Steamed bean pudding blended with peppers and warm Nigerian spices.", 250000, "sides", "", False),
            ("Akara & pap", "Crisp akara bean fritters with a comforting cup of smooth pap.", 350000, "breakfast-brunch", "", False),
            ("Chicken suya rice bowl", "Yaji-spiced grilled chicken over rice with fresh tomato and onion.", 680000, "nigerian-favourites", "", False),
            ("Chicken alfredo pasta", "Creamy fettuccine with grilled chicken, parmesan and herbs.", 850000, "international-favourites", "", False),
            ("Óriade beef burger & fries", "A seasoned beef patty with crisp lettuce, tomato and golden fries.", 950000, "international-favourites", "", False),
            ("Spaghetti bolognese", "Slow-simmered tomato and beef sauce over spaghetti, finished with herbs.", 780000, "international-favourites", "", False),
            ("Grilled chicken Caesar salad", "Grilled chicken, crisp lettuce, parmesan and creamy Caesar dressing.", 720000, "international-favourites", "", False),
            ("Pancakes & seasonal fruit", "Fluffy buttermilk pancakes with fresh fruit and a little syrup.", 550000, "breakfast-brunch", "", False),
            ("Chocolate brownie", "A rich cocoa brownie, baked with a soft centre.", 300000, "international-favourites", "", False),
        ]
        existing_items = {i.name: i for i in db.scalars(select(MenuItem).where(MenuItem.location_id == location.id))}
        generated_demo_images = {
            "/images/jollof.webp", "/images/egusi.webp", "/images/suya.webp",
            "/images/plantain.jpg", "/images/puff-puff.jpg", "/images/zobo.jpg",
            "/images/fried-rice.jpg", "/images/amala.jpg", "/images/pepper-soup.jpg",
            "/images/chicken-alfredo.jpg", "/images/burger.jpg",
        }
        for name, description, price, category, image, featured in dishes:
            if name in existing_items:
                item = existing_items[name]
                # Remove only the known synthetic sample assets; preserve uploaded photos.
                if item.image in generated_demo_images:
                    item.image = ""
                continue
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
        print("Sample catalog updated with missing dishes and Lagos LGAs. Demo prices and delivery fees require restaurant approval; no orders or customers were fabricated.")


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
