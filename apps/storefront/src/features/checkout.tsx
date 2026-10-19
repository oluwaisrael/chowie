"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Minus, ArrowRight, Trash2 } from "lucide-react";
import { useCart, cartTotal } from "@/lib/cart";
import { money, Order, Address } from "@/lib/types";
import { api, json } from "@/lib/api";
import { useCatalog, Loading, Empty, ErrorBox } from "@/components/common";
import { useAuth } from "@/components/providers";
import { useQuery } from "@tanstack/react-query";
export function CartPage() {
  const lines = useCart((s) => s.lines);
  const quantity = useCart((s) => s.quantity);
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);
  if (!ready) return <Loading />;
  if (!lines.length)
    return (
      <Empty
        title="Your bag is waiting."
        description="A comforting classic or a new favourite? Let’s find you something good."
      />
    );
  return (
    <div className="section page-section">
      <div className="checkout-heading">
        <span className="eyebrow">GOOD CHOICES, ALL ROUND</span>
        <h1>Your bag.</h1>
        <p>A little something to look forward to.</p>
      </div>
      <div className="two-column">
        <div>
          {lines.map((line) => (
            <article className="cart-item" key={line.key}>
              {line.image && (
                <img
                  src={line.image}
                  alt={line.name}
                  width="100"
                  height="110"
                />
              )}
              <div className="cart-item-content">
                <h3>
                  <Link href={`/menu/${line.item_id}`}>{line.name}</Link>
                </h3>
                <p>{line.modifierNames.join(", ") || "Just as it comes"}</p>
                <div className="quantity">
                  <button
                    onClick={() => quantity(line.key, line.quantity - 1)}
                    aria-label={`Decrease ${line.name}`}
                  >
                    <Minus size={14} />
                  </button>
                  <span>{line.quantity}</span>
                  <button
                    onClick={() => quantity(line.key, line.quantity + 1)}
                    disabled={line.quantity === 20}
                    aria-label={`Increase ${line.name}`}
                  >
                    <Plus size={14} />
                  </button>
                  <button
                    onClick={() => quantity(line.key, 0)}
                    aria-label={`Remove ${line.name}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <strong>{money(line.price * line.quantity)}</strong>
            </article>
          ))}
          <Link className="text-link" href="/menu" style={{ marginTop: 25 }}>
            A little more? Keep browsing <ArrowRight size={16} />
          </Link>
        </div>
        <aside className="summary">
          <h2>On the table.</h2>
          <div className="summary-row">
            <span>Subtotal estimate</span>
            <span>{money(cartTotal(lines))}</span>
          </div>
          <div className="summary-row">
            <span>Delivery</span>
            <span>Calculated at checkout</span>
          </div>
          <Link className="button" href="/checkout">
            Continue to checkout <ArrowRight size={17} />
          </Link>
          <p className="small muted">
            Final prices and availability are checked when your order is saved.
            Pay online securely through Paystack after placing your order.
          </p>
        </aside>
      </div>
    </div>
  );
}
const schema = z
  .object({
    name: z.string().min(2, "Please enter your name.").max(100),
    email: z.string().email("Enter a valid email for your Paystack receipt."),
    phone: z
      .string()
      .regex(/^\+?[0-9 ()-]{7,25}$/, "Enter a valid phone number."),
    fulfillment: z.enum(["delivery", "pickup"]),
    payment_method: z.enum(["paystack", "pay_on_delivery"]),
    zone_id: z.string(),
    address: z.string().max(500),
    instructions: z.string().max(500),
  })
  .superRefine((data, ctx) => {
    if (data.fulfillment === "delivery") {
      if (!data.zone_id)
        ctx.addIssue({
          code: "custom",
          path: ["zone_id"],
          message: "Choose a delivery zone.",
        });
      if (data.address.trim().length < 5)
        ctx.addIssue({
          code: "custom",
          path: ["address"],
          message: "Enter your full delivery address.",
        });
    }
  });
type Form = z.infer<typeof schema>;
function checkoutCredentials() {
  const saved = sessionStorage.getItem("oriade-checkout");
  if (saved) return JSON.parse(saved) as { key: string; token: string };
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const token = btoa(String.fromCharCode(...bytes))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
  const value = { key: crypto.randomUUID(), token };
  sessionStorage.setItem("oriade-checkout", JSON.stringify(value));
  return value;
}
export function CheckoutPage() {
  const router = useRouter();
  const { user } = useAuth();
  const lines = useCart((s) => s.lines);
  const clear = useCart((s) => s.clear);
  const { data, isLoading, error } = useCatalog();
  const [ready, setReady] = useState(false);
  const [failure, setFailure] = useState("");
  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      fulfillment: "delivery",
      payment_method: "paystack",
      zone_id: "",
      address: "",
      instructions: "",
    },
  });
  const addresses = useQuery({
    queryKey: ["addresses"],
    queryFn: () => api<Address[]>("/addresses"),
    enabled: !!user,
  });
  useEffect(() => setReady(true), []);
  useEffect(() => {
    if (user) {
      if (!form.getValues("name")) form.setValue("name", user.name);
      if (!form.getValues("email")) form.setValue("email", user.email);
    }
  }, [user, form]);
  const fulfillment = useWatch({ control: form.control, name: "fulfillment" }),
    zoneId = useWatch({ control: form.control, name: "zone_id" }),
    paymentMethod = useWatch({ control: form.control, name: "payment_method" });
  const locationId = lines[0]?.location_id;
  const location = data?.locations.find((l) => l.id === locationId);
  const zones =
    data?.zones.filter((z) => z.location_id === locationId && z.active) || [];
  const fee =
    fulfillment === "delivery"
      ? zones.find((z) => z.id === zoneId)?.fee || 0
      : 0;
  async function submit(values: Form) {
    setFailure("");
    try {
      if (lines.some((l) => l.location_id !== locationId))
        throw new Error("Please order from one restaurant location at a time.");
      const creds = checkoutCredentials();
      const order = await api<Order>("/orders", {
        method: "POST",
        headers: { "Idempotency-Key": creds.key, "X-Order-Token": creds.token },
        body: json({
          ...values,
          location_id: locationId,
          zone_id: values.fulfillment === "delivery" ? values.zone_id : null,
          items: lines.map((l) => ({
            item_id: l.item_id,
            quantity: l.quantity,
            modifiers: l.modifiers,
          })),
        }),
      });
      sessionStorage.setItem(`oriade-order:${order.reference}`, creds.token);
      sessionStorage.removeItem("oriade-checkout");
      clear();
      router.push(`/orders/${order.reference}`);
    } catch (e) {
      setFailure((e as Error).message);
    }
  }
  if (!ready || isLoading) return <Loading />;
  if (error) return <ErrorBox message={error.message} />;
  if (!lines.length)
    return (
      <Empty
        title="Start with something delicious."
        description="Add your favourites to your bag before checking out."
      />
    );
  return (
    <div className="section page-section">
      <div className="checkout-heading">
        <span className="eyebrow">ALMOST AT THE TABLE</span>
        <h1>Make it yours.</h1>
        <p>
          Guest checkout is welcome. Pay securely with Paystack after your order
          is saved.
        </p>
      </div>
      <form onSubmit={form.handleSubmit(submit)}>
        <div className="two-column">
          <div>
            <section className="form-section">
              <h2>01. Your details</h2>
              <div className="form-grid">
                <label>
                  Your name
                  <input autoComplete="name" {...form.register("name")} />
                  <span className="field-error">
                    {form.formState.errors.name?.message}
                  </span>
                </label>
                <label>
                  Email for your receipt
                  <input
                    type="email"
                    autoComplete="email"
                    {...form.register("email")}
                  />
                  <span className="field-error">
                    {form.formState.errors.email?.message}
                  </span>
                </label>
                <label>
                  Phone number
                  <input
                    autoComplete="tel"
                    type="tel"
                    placeholder="0806 000 0000"
                    {...form.register("phone")}
                  />
                  <span className="field-error">
                    {form.formState.errors.phone?.message}
                  </span>
                </label>
              </div>
            </section>
            <section className="form-section">
              <h2>02. Your table or ours?</h2>
              <div className="segmented">
                <button
                  type="button"
                  className={fulfillment === "delivery" ? "active" : ""}
                  aria-pressed={fulfillment === "delivery"}
                  onClick={() => form.setValue("fulfillment", "delivery")}
                >
                  Deliver to me
                </button>
                <button
                  type="button"
                  className={fulfillment === "pickup" ? "active" : ""}
                  aria-pressed={fulfillment === "pickup"}
                  onClick={() => form.setValue("fulfillment", "pickup")}
                >
                  I’ll pick it up
                </button>
              </div>
              {fulfillment === "delivery" ? (
                <div className="form-grid">
                  {addresses.data && addresses.data.length > 0 && (
                    <label className="full">
                      Use a saved address
                      <select
                        defaultValue=""
                        onChange={(e) => {
                          const a = addresses.data.find(
                            (a) => a.id === e.target.value,
                          );
                          if (a) {
                            form.setValue("address", a.address);
                            form.setValue("phone", a.phone);
                          }
                        }}
                      >
                        <option value="">Enter a new address</option>
                        {addresses.data.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  <label className="full">
                    Delivery zone
                    <select {...form.register("zone_id")}>
                      <option value="">Select your area</option>
                      {zones.map((z) => (
                        <option key={z.id} value={z.id}>
                          {z.name} · {money(z.fee)}
                        </option>
                      ))}
                    </select>
                    <span className="small muted">Lagos coverage and sample delivery fee — please confirm availability and final fee with the restaurant.</span>
                    <span className="field-error">
                      {form.formState.errors.zone_id?.message}
                    </span>
                  </label>
                  <label className="full">
                    Full delivery address
                    <textarea
                      autoComplete="street-address"
                      placeholder="Street, building number, and a helpful landmark"
                      {...form.register("address")}
                    />
                    <span className="field-error">
                      {form.formState.errors.address?.message}
                    </span>
                  </label>
                </div>
              ) : (
                <div className="notice">
                  <strong>{location?.name}</strong>
                  <br />
                  {location?.address}
                  <br />
                  <span className="small">
                    Our team will confirm your pickup time on WhatsApp.
                  </span>
                </div>
              )}
            </section>
            <section className="form-section">
              <h2>03. How would you like to pay?</h2>
              <div className="segmented">
                <button type="button" className={paymentMethod === "paystack" ? "active" : ""} aria-pressed={paymentMethod === "paystack"} onClick={() => form.setValue("payment_method", "paystack")}>Pay online with Paystack</button>
                <button type="button" className={paymentMethod === "pay_on_delivery" ? "active" : ""} aria-pressed={paymentMethod === "pay_on_delivery"} onClick={() => form.setValue("payment_method", "pay_on_delivery")}>Pay on delivery</button>
              </div>
              <p className="small muted">Paystack becomes available after the restaurant confirms your order. Pay on delivery means you pay the restaurant when your order arrives or is collected.</p>
            </section>
            <section className="form-section">
              <h2>04. Anything else?</h2>
              <label>
                Special instructions <span className="muted">(optional)</span>
                <textarea
                  placeholder="Preferences or a delivery note. Please confirm allergies with our team."
                  {...form.register("instructions")}
                />
              </label>
              <span className="field-error">
                {form.formState.errors.instructions?.message}
              </span>
            </section>
            {failure && <ErrorBox message={failure} />}
          </div>
          <aside className="summary">
            <h2>Your order.</h2>
            {lines.map((l) => (
              <div key={l.key} className="summary-row">
                <span>
                  {l.quantity} × {l.name}
                  <br />
                  <small className="muted">{l.modifierNames.join(", ")}</small>
                </span>
                <span>{money(l.price * l.quantity)}</span>
              </div>
            ))}
            <div className="summary-row">
              <span>Subtotal estimate</span>
              <span>{money(cartTotal(lines))}</span>
            </div>
            <div className="summary-row">
              <span>Delivery</span>
              <span>
                {fulfillment === "pickup"
                  ? "Pickup · Free"
                  : zoneId
                    ? money(fee)
                    : "Choose a zone"}
              </span>
            </div>
            <div className="summary-row total">
              <span>Estimated total</span>
              <span>{money(cartTotal(lines) + fee)}</span>
            </div>
            <button className="button" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting
                ? "Saving your order…"
                : "Place order & continue"}
              <ArrowRight size={17} />
            </button>
            <p className="small muted">
              The server checks current prices and stock. You’ll see the
              verified total. You can also contact the restaurant on WhatsApp
              from the order tracking page.
            </p>
            <Link href="/cart" className="text-link">
              Edit your bag
            </Link>
          </aside>
        </div>
      </form>
    </div>
  );
}
