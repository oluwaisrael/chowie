"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useAuth } from "@/components/providers";
import { useCatalog, Loading, ErrorBox, Empty } from "@/components/common";
import { api, json } from "@/lib/api";
import { Order, Item, User, money, label } from "@/lib/types";
import { useLive } from "@/lib/live";
import { Plus, ArrowUpRight, Star, MessageCircle, MapPin } from "lucide-react";
export function StaffGuard({
  children,
  kitchen = false,
}: {
  children: React.ReactNode;
  kitchen?: boolean;
}) {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user)
    return (
      <Empty
        title="Welcome to the kitchen."
        description="Sign in with your staff account to continue."
        href="/login"
        action="Staff sign in"
      />
    );
  if (user.role === "customer" || (!kitchen && user.role === "kitchen"))
    return (
      <Empty
        title="This table is for the team."
        description="Your account does not have access to this workspace."
        href="/account"
        action="Back to your account"
      />
    );
  return <>{children}</>;
}
export function Workspace({
  children,
  title,
}: {
  children: React.ReactNode;
  title: string;
}) {
  const path = usePathname();
  const { user } = useAuth();
  const links = [
    ["/operations", "Overview"],
    ["/operations/orders", "Orders"],
    ["/operations/delivery", "Delivery"],
    ["/operations/messages", "Customer contact"],
    ["/operations/reviews", "Reviews"],
    ["/operations/menu", "Menu"],
    ["/operations/settings", "Settings"],
    ...(user?.role === "admin" ? [["/operations/staff", "Staff & audit"]] : []),
    ["/kitchen", "Kitchen ↗"],
  ];
  return (
    <div className="workspace">
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">ÓRIADE / RESTAURANT WORKSPACE</span>
          <h1>{title}</h1>
        </div>
        <span className="small muted">
          {user?.name} · {label(user?.role || "staff")}
        </span>
      </div>
      <nav className="tabs workspace-nav" aria-label="Operations navigation">
        {links.map(([href, name]) => (
          <Link
            key={href}
            href={href}
            className={path === href ? "active" : ""}
          >
            {name}
          </Link>
        ))}
      </nav>
      {children}
    </div>
  );
}
type Reports = {
  total_orders: number;
  submitted_order_value: number;
  confirmed_order_value: number;
  average_order_value: number;
  counts: Record<string, number>;
  popular: { name: string; quantity: number }[];
  daily: { date: string; orders: number }[];
  categories: { name: string; quantity: number }[];
  average_preparation_minutes: number | null;
  collected_revenue: number;
};
export function Overview() {
  const report = useQuery({
    queryKey: ["reports"],
    queryFn: () => api<Reports>("/admin/reports"),
  });
  const queue = useQuery({
    queryKey: ["staff-orders", false],
    queryFn: () => api<Order[]>("/orders"),
  });
  if (report.isLoading) return <Loading />;
  if (report.error) return <ErrorBox message={report.error.message} />;
  const r = report.data;
  if (!r) return null;
  return (
    <>
      <p className="muted small">
        Live operational data. Paystack totals include verified successful
        payments only.
      </p>
      <div className="stats">
        {[
          ["Total orders", r.total_orders],
          [
            "Confirmed, in progress",
            (r.counts.CONFIRMED || 0) +
              (r.counts.PREPARING || 0) +
              (r.counts.READY || 0) +
              (r.counts.OUT_FOR_DELIVERY || 0),
          ],
          ["Completed", r.counts.COMPLETED || 0],
          ["Cancelled", r.counts.CANCELLED || 0],
        ].map(([name, value]) => (
          <div className="stat" key={name}>
            <span>{name}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="stats">
        {[
          ["Submitted order value", money(r.submitted_order_value)],
          ["Confirmed order value", money(r.confirmed_order_value)],
          ["Average order value", money(r.average_order_value)],
          ["Paystack payments received", money(r.collected_revenue)],
          ["Awaiting confirmation", queue.data?.filter((o) => o.status === "PENDING_CONFIRMATION").length || 0],
          ["Out for delivery", queue.data?.filter((o) => o.status === "OUT_FOR_DELIVERY").length || 0],
          [
            "Average preparation",
            r.average_preparation_minutes !== null
              ? `${r.average_preparation_minutes.toFixed(1)} min`
              : "Not yet available",
          ],
        ].map(([name, value]) => (
          <div className="stat" key={name}>
            <span>{name}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <section className="panel" style={{ marginBottom: 24 }}>
        <div className="section-heading">
          <div>
            <h2>Needs attention</h2>
            <p className="muted small">New orders and deliveries currently in progress.</p>
          </div>
          <Link className="text-link" href="/operations/orders">Open all orders <ArrowUpRight size={15} /></Link>
        </div>
        {queue.isLoading ? <p className="muted">Loading the live order queue…</p> : queue.error ? <p className="muted">Order queue is temporarily unavailable.</p> : (
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th>Order</th><th>Customer</th><th>Status</th><th>Payment</th><th>Total</th></tr></thead>
              <tbody>
                {(queue.data || []).filter((o) => !["COMPLETED", "CANCELLED"].includes(o.status)).slice(0, 6).map((o) => (
                  <tr key={o.reference}>
                    <td><Link href="/operations/orders">{o.reference}</Link></td>
                    <td>{o.name || "Guest"}<br /><span className="muted">{o.phone}</span></td>
                    <td><span className={`badge ${o.status.toLowerCase()}`}>{label(o.status)}</span></td>
                    <td>{o.payment_status === "success" ? "Paystack paid" : o.payment_status === "pay_on_delivery" ? "Pay on delivery" : "Paystack unpaid"}</td>
                    <td>{money(o.total || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {queue.data?.every((o) => ["COMPLETED", "CANCELLED"].includes(o.status)) && <p className="muted">No open orders right now.</p>}
          </div>
        )}
      </section>
      <div className="workspace-grid">
        <div className="panel">
          <h2>Most ordered dishes</h2>
          {r.popular.length ? (
            r.popular.map((d) => (
              <div className="chart-bar" key={d.name}>
                <span>{d.name}</span>
                <i
                  style={{
                    width: `${(d.quantity / Math.max(...r.popular.map((p) => p.quantity))) * 100}%`,
                  }}
                />
                <b>{d.quantity}</b>
              </div>
            ))
          ) : (
            <p className="muted">No orders yet.</p>
          )}
        </div>
        <div className="panel">
          <h2>Orders by day</h2>
          {r.daily.length ? (
            r.daily.map((d) => (
              <div className="chart-bar" key={d.date}>
                <span>{d.date}</span>
                <i
                  style={{
                    width: `${(d.orders / Math.max(...r.daily.map((p) => p.orders))) * 100}%`,
                  }}
                />
                <b>{d.orders}</b>
              </div>
            ))
          ) : (
            <p className="muted">Your activity will appear here.</p>
          )}
        </div>
        <div className="panel">
          <h2>Portions by category</h2>
          {r.categories.map((c) => (
            <div className="summary-row" key={c.name}>
              <span>{c.name}</span>
              <b>{c.quantity}</b>
            </div>
          ))}
        </div>
        <div className="panel">
          <h2>A clear view of the numbers.</h2>
          <p className="muted small">
            Submitted value includes pending and cancelled orders. Confirmed
            value includes confirmed through completed orders and excludes
            cancellations. Paystack payment totals include verified successful
            charges; refunds are not processed automatically and must be handled
            from the Paystack dashboard.
          </p>
        </div>
      </div>
    </>
  );
}

type ReviewRow = {
  id: string;
  reference: string;
  customer_name: string;
  rating: number;
  message: string;
  published: boolean;
  created_at: string;
};
export function ReviewsWorkspace() {
  const client = useQueryClient();
  const reviews = useQuery({
    queryKey: ["admin-reviews"],
    queryFn: () => api<ReviewRow[]>("/admin/reviews"),
  });
  const [error, setError] = useState("");
  async function publish(review: ReviewRow, published: boolean) {
    setError("");
    try {
      await api(`/admin/reviews/${review.id}`, {
        method: "PATCH",
        body: json({ published }),
      });
      await client.invalidateQueries({ queryKey: ["admin-reviews"] });
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (reviews.isLoading) return <Loading />;
  if (reviews.error) return <ErrorBox message={reviews.error.message} />;
  return (
    <>
      <p className="muted small">
        Reviews come from completed orders. New reviews stay hidden until a
        staff member publishes them.
      </p>
      {error && <ErrorBox message={error} />}
      <div className="workspace-grid">
        {reviews.data?.map((review) => (
          <article className="panel" key={review.id}>
            <div className="summary-row">
              <strong>{review.customer_name}</strong>
              <span className="badge">
                {"★".repeat(review.rating)}
                {"☆".repeat(5 - review.rating)}
              </span>
            </div>
            <p>{review.message}</p>
            <p className="small muted">
              Order {review.reference} ·{" "}
              {new Date(review.created_at).toLocaleDateString()}
            </p>
            <button
              className={review.published ? "text-link" : "button"}
              onClick={() => publish(review, !review.published)}
            >
              {review.published ? "Unpublish review" : "Publish review"}
            </button>
          </article>
        ))}
      </div>
      {!reviews.data?.length && (
        <div className="empty">
          <Star />
          <h2>No reviews yet.</h2>
          <p>
            After a delivery is marked complete, customers can leave a review
            from their order tracking page.
          </p>
        </div>
      )}
    </>
  );
}

export function CustomerContactWorkspace() {
  const orders = useQuery({
    queryKey: ["staff-orders", false],
    queryFn: () => api<Order[]>("/orders"),
  });
  if (orders.isLoading) return <Loading />;
  if (orders.error) return <ErrorBox message={orders.error.message} />;
  return (
    <>
      <p className="notice">
        <MessageCircle
          size={16}
          style={{ display: "inline", verticalAlign: "middle", marginRight: 8 }}
        />
        WhatsApp is not connected as an inbox. This page lets your team start an
        outbound WhatsApp chat; replies will appear in WhatsApp, not here.
      </p>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Order</th>
              <th>Delivery</th>
              <th>Status</th>
              <th>Contact</th>
            </tr>
          </thead>
          <tbody>
            {(orders.data || []).map((order) => (
              <tr key={order.reference}>
                <td>
                  {order.name}
                  <br />
                  <span className="muted">{order.phone}</span>
                </td>
                <td>{order.reference}</td>
                <td>{order.address || "Pickup"}</td>
                <td>
                  <span className={`badge ${order.status.toLowerCase()}`}>
                    {label(order.status)}
                  </span>
                </td>
                <td>
                  <a
                    className="text-link"
                    href={`https://wa.me/${(order.phone || "").replace(/\D/g, "")}?text=${encodeURIComponent(`Hello ${order.name}, we are contacting you about order ${order.reference}.`)}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Message on WhatsApp <ArrowUpRight size={14} />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!orders.data?.length && (
        <div className="empty">
          <h2>No customer orders yet.</h2>
        </div>
      )}
    </>
  );
}
const nextStatuses = (o: Order, kitchen: boolean) => {
  if (kitchen)
    return o.status === "CONFIRMED"
      ? ["PREPARING"]
      : o.status === "PREPARING"
        ? ["READY"]
        : [];
  const next: Record<string, string[]> = {
    PENDING_CONFIRMATION: ["CONFIRMED", "CANCELLED"],
    CONFIRMED: ["PREPARING", "CANCELLED"],
    PREPARING: ["READY", "CANCELLED"],
    READY: [
      o.fulfillment === "pickup" ? "COMPLETED" : "OUT_FOR_DELIVERY",
      "CANCELLED",
    ],
    OUT_FOR_DELIVERY: ["COMPLETED", "CANCELLED"],
  };
  return next[o.status] || [];
};
export function OrdersWorkspace({
  kitchen = false,
  deliveryOnly = false,
}: {
  kitchen?: boolean;
  deliveryOnly?: boolean;
}) {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["staff-orders", kitchen],
    queryFn: () => api<Order[]>("/orders"),
  });
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [emailBusy, setEmailBusy] = useState("");
  const [emailSent, setEmailSent] = useState("");
  const [search, setSearch] = useState("");
  const [clock, setClock] = useState(0);
  useEffect(() => {
    setClock(Date.now());
    const t = setInterval(() => setClock(Date.now()), 30000);
    return () => clearInterval(t);
  }, []);
  const live = useLive<Order[]>("/events", (data) =>
    client.setQueryData(["staff-orders", kitchen], data),
  );
  async function change(order: Order, status: string) {
    setBusy(order.reference);
    setError("");
    try {
      await api(`/orders/${order.reference}/status`, {
        method: "PATCH",
        body: json({ status, version: order.version }),
      });
      await query.refetch();
      await client.invalidateQueries({ queryKey: ["reports"] });
    } catch (e) {
      setError((e as Error).message);
      void query.refetch();
    } finally {
      setBusy("");
    }
  }
  async function resendEmail(order: Order) {
    setEmailBusy(order.reference);
    setError("");
    try {
      await api(`/admin/orders/${order.reference}/email`, { method: "POST" });
      setEmailSent(`Order update sent to ${order.email}.`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEmailBusy("");
    }
  }
  if (query.isLoading) return <Loading />;
  if (query.error) return <ErrorBox message={query.error.message} />;
  const orders =
    query.data?.filter(
      (o) =>
        (filter === "all" || o.status === filter) &&
        (!search || `${o.reference} ${o.name || ""} ${o.phone || ""} ${o.address || ""}`.toLowerCase().includes(search.toLowerCase())) &&
        (!kitchen || ["CONFIRMED", "PREPARING", "READY"].includes(o.status)) &&
        (!deliveryOnly || o.fulfillment === "delivery"),
    ) || [];
  if (kitchen || deliveryOnly)
    orders.sort((a, b) => a.created_at.localeCompare(b.created_at));
  const filters = kitchen
    ? ["all", "CONFIRMED", "PREPARING", "READY"]
    : deliveryOnly
      ? [
          "all",
          "PENDING_CONFIRMATION",
          "CONFIRMED",
          "PREPARING",
          "READY",
          "OUT_FOR_DELIVERY",
          "COMPLETED",
          "CANCELLED",
        ]
      : [
          "all",
          "PENDING_CONFIRMATION",
          "CONFIRMED",
          "PREPARING",
          "READY",
          "COMPLETED",
          "CANCELLED",
        ];
  return (
    <>
      {deliveryOnly && (
        <div className="stats">
          {["CONFIRMED", "PREPARING", "READY", "OUT_FOR_DELIVERY"].map((s) => (
            <div className="stat" key={s}>
              <span>{label(s)}</span>
              <strong>
                {query.data?.filter(
                  (o) => o.fulfillment === "delivery" && o.status === s,
                ).length || 0}
              </strong>
            </div>
          ))}
        </div>
      )}
      <div className="filter-row">
        <div className="tabs">
          {filters.map((s) => (
            <button
              key={s}
              className={filter === s ? "active" : ""}
              onClick={() => setFilter(s)}
            >
              {label(s)}
            </button>
          ))}
        </div>
        <span className="live-indicator">
          <i />
          {live ? "Live queue" : "Reconnecting…"}
        </span>
      </div>
      {emailSent && <div className="notice" role="status">{emailSent}</div>}
      {!kitchen && <label className="full">Find an order, customer or delivery area<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Order reference, name, phone or area" /></label>}
      {error && <ErrorBox message={error} />}{" "}
      {!orders.length ? (
        <div className="empty">
          <h2>
            {kitchen
              ? "A quiet kitchen."
              : deliveryOnly
                ? "No matching deliveries."
                : "No orders here yet."}
          </h2>
          <p>
            {kitchen
              ? "Confirmed orders will appear automatically."
              : "Orders will appear here as customers submit them."}
          </p>
        </div>
      ) : (
        <div className={kitchen ? "kitchen-grid" : "workspace-grid"}>
          {orders.map((o) => (
            <article className="kitchen-card" key={o.reference}>
              <header>
                <strong className="reference">{o.reference}</strong>
                <span className="age">
                  {Math.max(
                    0,
                    Math.floor(
                      (clock - new Date(o.created_at).getTime()) / 60000,
                    ),
                  )}{" "}
                  min ago
                </span>
              </header>
              <span className={`badge ${o.status.toLowerCase()}`}>
                {label(o.status)}
              </span>
              <span className="small muted" style={{ marginLeft: 10 }}>
                {label(o.fulfillment)}
              </span>
              {!kitchen && (
                <span
                  className={`badge ${o.payment_status === "success" ? "completed" : "pending_confirmation"}`}
                  style={{ marginLeft: 8 }}
                >
                  {o.payment_status === "success" ? "Paystack · paid" : o.payment_status === "pay_on_delivery" ? "Pay on delivery" : "Paystack · unpaid"}
                </span>
              )}
              <ul>
                {o.items.map((i, n) => (
                  <li key={n}>
                    <strong>{i.quantity} ×</strong> {i.name}
                    {i.modifiers.length > 0 && (
                      <small>{i.modifiers.map((m) => m.name).join(", ")}</small>
                    )}
                  </li>
                ))}
              </ul>
              {o.instructions && <div className="notice">{o.instructions}</div>}
              {!kitchen && (
                <div className="small">
                  <strong>{o.name}</strong>
                  <br />
                  <a href={`tel:${o.phone}`}>{o.phone}</a>
                  <p>
                    {deliveryOnly && (
                      <MapPin size={14} style={{ display: "inline" }} />
                    )}{" "}
                    {o.address || "Pickup order"}
                  </p>
                  <div className="summary-row">
                    <span>Order value</span>
                    <b>{money(o.total || 0)}</b>
                  </div>
                  {o.email && <button className="text-link" disabled={emailBusy === o.reference} onClick={() => void resendEmail(o)}>{emailBusy === o.reference ? "Sending order email…" : "Resend order email"}</button>}
                </div>
              )}
              <div className="stack">
                {nextStatuses(o, kitchen).map((status) => (
                  <button
                    key={status}
                    className={status === "CANCELLED" ? "text-link" : "button"}
                    disabled={busy === o.reference}
                    onClick={() => change(o, status)}
                  >
                    {status === "CONFIRMED"
                      ? "Confirm order"
                      : status === "PREPARING"
                        ? "Accept & start preparing"
                        : status === "READY"
                          ? "Mark ready"
                          : status === "OUT_FOR_DELIVERY"
                            ? "Dispatch delivery"
                            : status === "CANCELLED"
                              ? "Cancel order"
                              : `Mark ${label(status).toLowerCase()}`}
                  </button>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
type ItemForm = {
  name: string;
  description: string;
  price: number;
  category_id: string;
  location_id: string;
  image: string;
  available: boolean;
  featured: boolean;
};
export function MenuWorkspace() {
  const query = useCatalog();
  const client = useQueryClient();
  const [editing, setEditing] = useState<Item | null | undefined>();
  const [mods, setMods] = useState<
    { id?: string; name: string; price: number; available: boolean }[]
  >([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [stock, setStock] = useState("");
  const form = useForm<ItemForm>();
  function edit(item: Item | null) {
    setEditing(item);
    setError("");
    setSuccess("");
    setStock("");
    form.reset(
      item
        ? {
            name: item.name,
            description: item.description,
            price: item.price / 100,
            category_id: item.category_id,
            location_id: item.location_id,
            image: item.image,
            available: item.available,
            featured: item.featured,
          }
        : {
            name: "",
            description: "",
            price: 0,
            category_id: query.data?.categories[0]?.id,
            location_id: query.data?.locations[0]?.id,
            image: "",
            available: true,
            featured: false,
          },
    );
    setMods(item?.modifiers.map((m) => ({ ...m, price: m.price / 100 })) || []);
  }
  async function save(values: ItemForm) {
    setError("");
    try {
      const result = await api<{ id: string }>(
        editing ? `/admin/items/${editing.id}` : "/admin/items",
        {
          method: editing ? "PUT" : "POST",
          body: json({
            ...values,
            price: Math.round(Number(values.price) * 100),
            modifiers: mods.map((m) => ({
              ...m,
              price: Math.round(m.price * 100),
            })),
          }),
        },
      );
      if (stock !== "")
        await api(`/admin/items/${result.id}/stock`, {
          method: "PUT",
          body: json({
            remaining: stock === "unlimited" ? null : Number(stock),
          }),
        });
      setEditing(undefined);
      setSuccess("Menu updated.");
      void client.invalidateQueries({ queryKey: ["catalog"] });
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function upload(file: File) {
    setUploading(true);
    setError("");
    try {
      const data = new FormData();
      data.set("file", file);
      const result = await api<{ url: string }>("/admin/images", {
        method: "POST",
        body: data,
      });
      form.setValue("image", result.url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }
  if (query.isLoading) return <Loading />;
  if (query.error) return <ErrorBox message={query.error.message} />;
  return (
    <>
      {success && <div className="notice">{success}</div>}
      {error && <ErrorBox message={error} />}
      <div className="section-heading">
        <p className="muted small">
          Manage dishes, add-ons, availability and portion limits.
        </p>
        <button className="button" onClick={() => edit(null)}>
          <Plus size={16} /> Add a dish
        </button>
      </div>
      {editing !== undefined ? (
        <div className="panel">
          <h2>{editing ? "Edit dish" : "A new favourite"}</h2>
          <form className="workspace-form" onSubmit={form.handleSubmit(save)}>
            <div className="form-grid">
              <label>
                Dish name
                <input required maxLength={120} {...form.register("name")} />
              </label>
              <label>
                Price (₦)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  {...form.register("price")}
                />
              </label>
              <label>
                Category
                <select {...form.register("category_id")}>
                  {query.data?.categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Restaurant location
                <select {...form.register("location_id")}>
                  {query.data?.locations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="full">
                Description
                <textarea
                  required
                  minLength={5}
                  maxLength={1000}
                  {...form.register("description")}
                />
              </label>
              <label>
                Image URL
                <input
                  placeholder="https://… or /images/…"
                  {...form.register("image")}
                />
              </label>
              <label>
                Upload food photograph
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  disabled={uploading}
                  onChange={(e) => {
                    if (e.target.files?.[0]) void upload(e.target.files[0]);
                  }}
                />
                {uploading && <span className="small">Uploading…</span>}
              </label>
              <label>
                Stock update
                <input
                  placeholder="Blank = unchanged; unlimited or a number"
                  value={stock}
                  onChange={(e) => setStock(e.target.value)}
                />
              </label>
              <div className="stack">
                <label className="checkbox">
                  <input type="checkbox" {...form.register("available")} />{" "}
                  Available to order
                </label>
                <label className="checkbox">
                  <input type="checkbox" {...form.register("featured")} />{" "}
                  Feature on homepage
                </label>
              </div>
            </div>
            <h3>Optional add-ons</h3>
            {mods.map((m, i) => (
              <div className="form-grid" key={i}>
                <label>
                  Add-on name
                  <input
                    required
                    value={m.name}
                    onChange={(e) =>
                      setMods(
                        mods.map((m, n) =>
                          n === i ? { ...m, name: e.target.value } : m,
                        ),
                      )
                    }
                  />
                </label>
                <label>
                  Add-on price (₦)
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    value={m.price}
                    onChange={(e) =>
                      setMods(
                        mods.map((m, n) =>
                          n === i ? { ...m, price: Number(e.target.value) } : m,
                        ),
                      )
                    }
                  />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={m.available}
                    onChange={(e) =>
                      setMods(
                        mods.map((m, n) =>
                          n === i ? { ...m, available: e.target.checked } : m,
                        ),
                      )
                    }
                  />{" "}
                  Available
                </label>
              </div>
            ))}
            <button
              className="text-link"
              type="button"
              onClick={() =>
                setMods([...mods, { name: "", price: 0, available: true }])
              }
            >
              Add an extra
            </button>
            <div style={{ display: "flex", gap: 15 }}>
              <button
                className="button"
                disabled={form.formState.isSubmitting || uploading}
              >
                Save dish
              </button>
              <button
                type="button"
                className="text-link"
                onClick={() => setEditing(undefined)}
              >
                Close
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Dish</th>
                <th>Price</th>
                <th>Availability</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.items.map((i) => (
                <tr key={i.id}>
                  <td>{i.name}</td>
                  <td>{money(i.price)}</td>
                  <td>{i.available ? "Available" : "Unavailable"}</td>
                  <td>
                    <button onClick={() => edit(i)}>Edit dish</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
export function SettingsWorkspace() {
  const query = useCatalog();
  const { user } = useAuth();
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  async function save(
    event: React.FormEvent<HTMLFormElement>,
    path: string,
    type: "category" | "location" | "zone",
  ) {
    event.preventDefault();
    const element = event.currentTarget;
    const values = Object.fromEntries(new FormData(element));
    const body =
      type === "zone"
        ? {
            ...values,
            fee: Math.round(Number(values.fee) * 100),
            active: values.active === "on",
          }
        : type === "location"
          ? { ...values, active: values.active === "on" }
          : values;
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      await api(path, {
        method: path.split("/").length > 3 ? "PUT" : "POST",
        body: json(body),
      });
      await query.refetch();
      setSuccess("Settings saved.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (query.isLoading) return <Loading />;
  if (query.error) return <ErrorBox message={query.error.message} />;
  const c = query.data;
  return (
    <>
      {error && <ErrorBox message={error} />}{" "}
      {success && <div className="notice">{success}</div>}
      <div className="workspace-grid">
        <section className="panel">
          <h2>Categories</h2>
          {[...(c?.categories || []), { id: "", name: "", slug: "" }].map(
            (cat) => (
              <form
                className="workspace-form"
                key={cat.id || "new"}
                onSubmit={(e) =>
                  save(
                    e,
                    `/admin/categories${cat.id ? "/" + cat.id : ""}`,
                    "category",
                  )
                }
              >
                <div className="form-grid">
                  <label>
                    Name
                    <input
                      name="name"
                      required
                      defaultValue={cat.name}
                      placeholder="New category"
                    />
                  </label>
                  <label>
                    URL slug
                    <input
                      name="slug"
                      required
                      pattern="[a-z0-9]+(-[a-z0-9]+)*"
                      defaultValue={cat.slug}
                      placeholder="soups-swallows"
                    />
                  </label>
                </div>
                <button className="text-link" disabled={busy}>
                  {cat.id ? "Save category" : "Add category"}
                </button>
                <hr
                  style={{
                    border: 0,
                    borderTop: "1px solid var(--line)",
                    margin: "10px 0 20px",
                  }}
                />
              </form>
            ),
          )}
        </section>
        <section className="panel">
          <h2>Delivery zones</h2>
          <p className="small muted">The seeded Lagos areas and ₦2,000 sample fees are placeholders. Set the real coverage and fee for each location here before launch.</p>
          {[
            ...(c?.zones || []),
            {
              id: "",
              name: "",
              fee: 0,
              location_id: c?.locations[0]?.id || "",
              active: true,
            },
          ].map((z) => (
            <form
              className="workspace-form"
              key={z.id || "new"}
              onSubmit={(e) =>
                save(e, `/admin/zones${z.id ? "/" + z.id : ""}`, "zone")
              }
            >
              <label>
                Zone name
                <input name="name" defaultValue={z.name} required />
              </label>
              <div className="form-grid">
                <label>
                  Delivery fee (₦)
                  <input
                    name="fee"
                    type="number"
                    min="0"
                    step="0.01"
                    defaultValue={z.fee / 100}
                    required
                  />
                </label>
                <label>
                  Location
                  <select name="location_id" defaultValue={z.location_id}>
                    {c?.locations.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label className="checkbox">
                <input
                  name="active"
                  type="checkbox"
                  defaultChecked={z.active}
                />{" "}
                Active
              </label>
              <button className="text-link" disabled={busy}>
                {z.id ? "Save zone" : "Add zone"}
              </button>
              <hr
                style={{
                  border: 0,
                  borderTop: "1px solid var(--line)",
                  margin: "10px 0 20px",
                }}
              />
            </form>
          ))}
        </section>
        {user?.role === "admin" && (
          <section className="panel">
            <h2>Restaurant locations</h2>
            {[
              ...(c?.locations || []),
              { id: "", name: "", address: "", active: true },
            ].map((l) => (
              <form
                className="workspace-form"
                key={l.id || "new"}
                onSubmit={(e) =>
                  save(
                    e,
                    `/admin/locations${l.id ? "/" + l.id : ""}`,
                    "location",
                  )
                }
              >
                <label>
                  Name
                  <input name="name" defaultValue={l.name} required />
                </label>
                <label>
                  Pickup address
                  <textarea
                    name="address"
                    defaultValue={l.address}
                    minLength={5}
                    required
                  />
                </label>
                <label className="checkbox">
                  <input
                    name="active"
                    type="checkbox"
                    defaultChecked={l.active}
                  />{" "}
                  Open for orders
                </label>
                <button className="text-link" disabled={busy}>
                  {l.id ? "Save location" : "Add location"}
                </button>
                <hr
                  style={{
                    border: 0,
                    borderTop: "1px solid var(--line)",
                    margin: "10px 0 20px",
                  }}
                />
              </form>
            ))}
          </section>
        )}
        <section className="panel">
          <h2>WhatsApp ordering</h2>
          <p className="small muted">
            The destination is configured on the API server through
            WHATSAPP_NUMBER. The default is +234 806 651 4361. Click-to-chat is
            enabled; automatic Cloud API messaging is not connected.
          </p>
          <p className="small muted">
            Image uploads require S3-compatible storage. Password reset emails
            require SMTP. Neither service is simulated when credentials are
            missing.
          </p>
        </section>
      </div>
    </>
  );
}
export function StaffWorkspace() {
  const { user } = useAuth();
  const users = useQuery({
    queryKey: ["users"],
    queryFn: () => api<User[]>("/admin/users"),
    enabled: user?.role === "admin",
  });
  const audit = useQuery({
    queryKey: ["audit"],
    queryFn: () =>
      api<{ id: string; action: string; target: string; created_at: string }[]>(
        "/admin/audit",
      ),
    enabled: user?.role === "admin",
  });
  const [error, setError] = useState("");
  async function update(u: User, role: User["role"], active: boolean) {
    try {
      await api(`/admin/users/${u.id}`, {
        method: "PATCH",
        body: json({ role, active }),
      });
      await users.refetch();
      await audit.refetch();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (user?.role !== "admin")
    return <ErrorBox message="Only administrators can manage staff access." />;
  return (
    <>
      {error && <ErrorBox message={error} />}
      <p className="small muted">
        Staff register an account first. Assign access here. Changing access
        invalidates all of that user’s sessions.
      </p>
      {users.error && <ErrorBox message={users.error.message} />}
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Access</th>
            </tr>
          </thead>
          <tbody>
            {users.data?.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>
                  <select
                    aria-label={`Role for ${u.name}`}
                    value={u.role}
                    disabled={u.id === user.id}
                    onChange={(e) =>
                      update(
                        u,
                        e.target.value as User["role"],
                        u.active !== false,
                      )
                    }
                  >
                    {["customer", "operator", "kitchen", "admin"].map((r) => (
                      <option key={r}>{r}</option>
                    ))}
                  </select>
                </td>
                <td>
                  <button
                    disabled={u.id === user.id}
                    onClick={() => update(u, u.role, u.active === false)}
                  >
                    {u.active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 style={{ fontSize: 30, marginTop: 40 }}>Recent audit activity</h2>
      {audit.error && <ErrorBox message={audit.error.message} />}
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>When</th>
              <th>Action</th>
              <th>Record</th>
            </tr>
          </thead>
          <tbody>
            {audit.data?.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleString()}</td>
                <td>{a.action}</td>
                <td>{a.target}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
export function KitchenPage() {
  return (
    <StaffGuard kitchen>
      <div className="workspace">
        <div className="workspace-heading">
          <div>
            <span className="eyebrow">ÓRIADE / AT THE PASS</span>
            <h1>The kitchen.</h1>
          </div>
          <Link className="text-link" href="/operations">
            Operations <ArrowUpRight size={16} />
          </Link>
        </div>
        <p className="muted small">
          Oldest orders first. Only confirmed orders enter this queue. Customer
          contact details are hidden from kitchen accounts.
        </p>
        <OrdersWorkspace kitchen />
      </div>
    </StaffGuard>
  );
}
