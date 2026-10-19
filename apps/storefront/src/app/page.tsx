import { ArrowRight, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { Featured, PublishedReviews } from "@/features/menu";
import { serverCatalog } from "@/lib/server";

export default async function Home() {
  const catalog = await serverCatalog();

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">ÓRIADE · NIGERIAN KITCHEN · LAGOS</span>
          <h1>Nigerian food,<br />made fresh.</h1>
          <p>Jollof, soups, grills and more. Order for delivery or pickup.</p>
          <Link href="/menu" className="button">
            Browse the menu <ArrowRight size={18} />
          </Link>
          <div className="hero-note">Prepared in Lagos. Confirmed by our team.</div>
        </div>
        <div className="hero-menu-panel" aria-label="A few dishes from our menu">
          <span className="eyebrow">ON THE MENU</span>
          <ul>
            <li>Jollof rice & chicken</li>
            <li>Egusi & pounded yam</li>
            <li>Suya, plantain & more</li>
          </ul>
          <Link href="/menu" className="text-link">
            See all dishes <ArrowUpRight size={16} />
          </Link>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">THE MENU</span>
            <h2>Good food for the table.</h2>
          </div>
          <Link className="text-link" href="/menu">
            Browse all dishes <ArrowRight size={18} />
          </Link>
        </div>
        <Featured initialData={catalog} />
      </section>

      <PublishedReviews />

      <section className="story" id="story">
        <div className="story-intro">
          <span className="eyebrow">ABOUT ÓRIADE</span>
          <h2>Food is better shared.</h2>
          <p>We make Nigerian favourites and familiar international dishes for everyday meals and get-togethers.</p>
          <p>Choose what you like, tell us where it’s going, and our team will confirm the order with you.</p>
          <Link href="/menu" className="text-link">
            Choose your meal <ArrowRight size={18} />
          </Link>
        </div>
        <div className="story-details">
          <div><strong>01</strong><span>Choose your dishes</span></div>
          <div><strong>02</strong><span>Select delivery or pickup</span></div>
          <div><strong>03</strong><span>Track your order</span></div>
        </div>
      </section>

      <section className="section delivery-summary" id="visit">
        <span className="eyebrow">DELIVERY & PICKUP</span>
        <h2>Choose what works for you.</h2>
        <p>Choose a Lagos delivery area or pickup at checkout. Our team will confirm availability and the final delivery fee.</p>
      </section>

      <section className="final-cta">
        <div>
          <span className="eyebrow">READY TO ORDER?</span>
          <h2>See what’s cooking.</h2>
        </div>
        <Link href="/menu" className="button button-cream">
          View the menu <ArrowUpRight size={18} />
        </Link>
      </section>
    </>
  );
}
