"use client";
import { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, json } from "@/lib/api";
import { Order, money, label } from "@/lib/types";
import { useLive } from "@/lib/live";
import { useAuth } from "@/components/providers";
import { Loading, ErrorBox } from "@/components/common";
import { ArrowUpRight, Check } from "lucide-react";
export function OrderPage({ reference }: { reference: string }) {
  const { loading: authLoading } = useAuth();
  const [token, setToken] = useState<string | undefined>();
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [paymentMessage, setPaymentMessage] = useState("");
  const [paying, setPaying] = useState(false);
  const [paymentEmail, setPaymentEmail] = useState("");
  const callbackHandled = useRef(false);
  const client = useQueryClient();
  useEffect(() => {
    setToken(sessionStorage.getItem(`oriade-order:${reference}`) || undefined);
    setReady(true);
  }, [reference]);
  const query = useQuery({
    queryKey: ["order", reference],
    queryFn: () =>
      api<Order>(`/orders/${reference}`, {
        headers: token ? { "X-Order-Token": token } : {},
      }),
    enabled: ready && !authLoading,
    retry: false,
    refetchInterval: 5000,
  });
  const connected = useLive<Order>(
    query.data ? `/events?reference=${encodeURIComponent(reference)}` : null,
    (data) => client.setQueryData(["order", reference], data),
    token,
  );
  useEffect(() => {
    const paystackReference = new URLSearchParams(window.location.search).get(
      "reference",
    );
    if (!ready || authLoading || !paystackReference || callbackHandled.current)
      return;
    callbackHandled.current = true;
    window.history.replaceState({}, "", window.location.pathname);
    setPaymentMessage("Checking your payment directly with Paystack…");
    void api<{ status: string }>(`/orders/${reference}/payment/verify`, {
      method: "POST",
      headers: token ? { "X-Order-Token": token } : {},
      body: json({ reference: paystackReference }),
    })
      .then((result) => {
        setPaymentMessage(
          result.status === "success"
            ? "Payment confirmed. Thank you!"
            : `Payment status: ${label(result.status)}.`,
        );
        void client.invalidateQueries({ queryKey: ["order", reference] });
      })
      .catch((e: Error) => setPaymentMessage(e.message));
  }, [ready, authLoading, token, reference, client]);
  async function payWithPaystack() {
    setPaying(true);
    setError("");
    try {
      const result = await api<{ authorization_url: string }>(
        `/orders/${reference}/payment/initialize`,
        {
          method: "POST",
          headers: token ? { "X-Order-Token": token } : {},
          body: json({ email: query.data?.email || paymentEmail || null }),
        },
      );
      window.location.assign(result.authorization_url);
    } catch (e) {
      setError((e as Error).message);
      setPaying(false);
    }
  }
  async function handoff() {
    setError("");
    try {
      await api(`/orders/${reference}/handoff`, {
        method: "POST",
        headers: token ? { "X-Order-Token": token } : {},
      });
      if (query.data?.whatsapp_url)
        window.location.assign(query.data.whatsapp_url);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (!ready || authLoading || query.isLoading) return <Loading />;
  if (query.error)
    return (
      <div className="section">
        <ErrorBox message={query.error.message} />
        <p className="muted">
          Guest access is kept in the browser tab used for checkout. Sign in if
          this order belongs to your account.
        </p>
      </div>
    );
  const order = query.data;
  if (!order) return null;
  return (
    <div className="section page-section">
      <div className="order-head">
        <div>
          <span className="eyebrow">YOUR ORDER, SAFELY SAVED</span>
          <h1>
            {order.status === "PENDING_CONFIRMATION"
              ? "One last hello."
              : "Good things are on the way."}
          </h1>
          <p className="muted small">
            {order.reference} · {new Date(order.created_at).toLocaleString()}
          </p>
        </div>
        <span className={`badge ${order.status.toLowerCase()}`}>
          {label(order.status)}
        </span>
      </div>
      {order.status === "PENDING_CONFIRMATION" && (
        <div className="notice">
          <Check size={17} style={{ display: "inline", marginRight: 8 }} /> Your
          order is saved, but not yet confirmed. Send the summary on WhatsApp so
          our team can confirm availability and next steps.
        </div>
      )}
      <div className="two-column">
        <div>
          <h2 style={{ fontSize: 30 }}>At a glance.</h2>
          {order.items.map((i, n) => (
            <div className="summary-row" key={n}>
              <span>
                {i.quantity} × {i.name}
                <br />
                <small className="muted">
                  {i.modifiers.map((m) => m.name).join(", ")}
                </small>
              </span>
              <span>{money(i.unit_price * i.quantity)}</span>
            </div>
          ))}
          <div className="panel" style={{ marginTop: 30 }}>
            <h3>{label(order.fulfillment)} details</h3>
            <p>
              {order.name}
              <br />
              {order.phone}
              <br />
              {order.address}
            </p>
            {order.instructions && (
              <p className="small">Note: {order.instructions}</p>
            )}
          </div>
          <h2 style={{ fontSize: 30 }}>Follow your order.</h2>
          <div className="live-indicator">
            <i />
            {connected
              ? "Live updates connected"
              : "Reconnecting to live updates…"}
          </div>
          <ol className="timeline">
            {order.history.map((h, i) => (
              <li key={i}>
                {label(h.status)}
                <small>{new Date(h.at).toLocaleString()}</small>
              </li>
            ))}
          </ol>
          {order.status === "COMPLETED" && (
            <ReviewForm reference={reference} token={token} />
          )}
        </div>
        <aside className="summary">
          <h2>The final total.</h2>
          <div className="summary-row">
            <span>Subtotal</span>
            <span>{money(order.subtotal || 0)}</span>
          </div>
          <div className="summary-row">
            <span>Delivery</span>
            <span>{money(order.delivery_fee || 0)}</span>
          </div>
          <div className="summary-row total">
            <span>Total</span>
            <span>{money(order.total || 0)}</span>
          </div>
          {paymentMessage && (
            <div className="notice" role="status">
              {paymentMessage}
            </div>
          )}
          {order.payment_status === "pay_on_delivery" ? (
            <div className="notice">Pay on delivery selected. Please pay the restaurant when your order arrives or is collected.</div>
          ) : order.payment_status === "success" ? (
            <div className="notice">
              Payment received securely through Paystack.
            </div>
          ) : order.status === "PENDING_CONFIRMATION" ? (
            <div className="notice">
              Paystack payment becomes available after the restaurant confirms
              your order.
            </div>
          ) : order.payment_method !== "pay_on_delivery" && order.status !== "CANCELLED" && order.status !== "COMPLETED" ? (
            <>
              {!order.email && (
                <label>
                  Email for your Paystack receipt
                  <input
                    type="email"
                    autoComplete="email"
                    required
                    value={paymentEmail}
                    onChange={(event) => setPaymentEmail(event.target.value)}
                  />
                </label>
              )}
              <button
                className="button"
                onClick={payWithPaystack}
                disabled={paying || (!order.email && !paymentEmail)}
              >
                {paying
                  ? "Connecting to Paystack…"
                  : `Pay ${money(order.total || 0)} with Paystack`}
              </button>
            </>
          ) : null}
          {order.status !== "CANCELLED" && (
            <button className="button" onClick={handoff}>
              Contact us on WhatsApp <ArrowUpRight size={17} />
            </button>
          )}
          <p className="small muted">
            Paystack confirms payment on its secure checkout page. WhatsApp is a
            separate order-confirmation conversation; opening it does not send a
            message.
          </p>
          {error && <ErrorBox message={error} />}
        </aside>
      </div>
    </div>
  );
}

function ReviewForm({
  reference,
  token,
}: {
  reference: string;
  token?: string;
}) {
  const existing = useQuery({
    queryKey: ["order-review", reference],
    queryFn: () =>
      api<{
        id: string;
        rating: number;
        message: string;
        published: boolean;
      } | null>(`/orders/${reference}/review`, {
        headers: token ? { "X-Order-Token": token } : {},
      }),
  });
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api(`/orders/${reference}/review`, {
        method: "POST",
        headers: token ? { "X-Order-Token": token } : {},
        body: JSON.stringify({ rating, message }),
      });
      setDone(true);
      void existing.refetch();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (existing.isLoading)
    return (
      <div className="panel">
        <p className="muted">Loading review…</p>
      </div>
    );
  if (existing.data)
    return (
      <div className="panel">
        <h3>Thank you for your review.</h3>
        <p>
          {"★".repeat(existing.data.rating)}
          {"☆".repeat(5 - existing.data.rating)}
        </p>
        <p>{existing.data.message}</p>
        <small className="muted">
          Your review is{" "}
          {existing.data.published
            ? "published"
            : "waiting for the restaurant to review it"}
          .
        </small>
      </div>
    );
  if (done)
    return (
      <div className="notice">
        Thanks for sharing your experience. Your review is saved and awaiting
        approval.
      </div>
    );
  return (
    <form className="panel stack" onSubmit={submit}>
      <h3>How was your Óriade order?</h3>
      <label>
        Rating
        <select
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
        >
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>
              {n} {n === 1 ? "star" : "stars"}
            </option>
          ))}
        </select>
      </label>
      <label>
        Your review
        <textarea
          required
          minLength={5}
          maxLength={1000}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
      </label>
      {error && <ErrorBox message={error} />}
      <button className="button">Send review</button>
      <small className="muted">
        Reviews are checked by the restaurant before they appear publicly.
      </small>
    </form>
  );
}
