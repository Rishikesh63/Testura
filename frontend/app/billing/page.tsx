"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import { billingApi } from "@/lib/api";
import { CheckCircle, Zap } from "lucide-react";
import { toast } from "sonner";

declare global {
  interface Window {
    Razorpay: any;
  }
}

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "₹0",
    features: ["1 repo", "50 tests/month", "Dashboard access"],
    cta: "Current plan",
    disabled: true,
  },
  {
    id: "starter",
    name: "Starter",
    price: "₹999",
    features: ["3 repos", "500 tests/month", "Email alerts"],
    cta: "Upgrade to Starter",
    disabled: false,
    highlight: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: "₹2,499",
    features: ["10 repos", "Unlimited tests", "Priority support"],
    cta: "Upgrade to Pro",
    disabled: false,
    highlight: true,
  },
];

export default function BillingPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState("free");
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    // Load Razorpay script
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    document.body.appendChild(script);

    // Get current user + plan
    getSupabase().auth.getSession().then(async ({ data }) => {
      if (!data.session) { router.push("/"); return; }
      const uid = data.session.user.id;
      setUserId(uid);
      const { data: planData } = await billingApi.getPlan(uid);
      setCurrentPlan(planData.plan);
    });
  }, [router]);

  async function handleUpgrade(planId: string) {
    if (!userId) return;
    setLoading(planId);
    try {
      const { data: order } = await billingApi.createOrder(planId, userId);

      const options = {
        key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
        amount: order.amount,
        currency: order.currency,
        name: "Testura",
        description: order.name,
        order_id: order.order_id,
        handler: async (response: any) => {
          try {
            await billingApi.verify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              plan: planId,
              user_id: userId,
            });
            setCurrentPlan(planId);
            toast.success(`Upgraded to ${planId} plan!`);
          } catch {
            toast.error("Payment verification failed. Contact support.");
          }
        },
        prefill: {},
        theme: { color: "#2563eb" },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch {
      toast.error("Failed to create order. Try again.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-3">
        <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-gray-700 text-sm">
          ← Dashboard
        </button>
        <div className="flex items-center gap-2 font-bold text-lg">
          <Zap className="text-blue-600" size={18} /> Billing
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-bold text-center mb-2">Choose your plan</h1>
        <p className="text-center text-gray-500 mb-12">
          Current plan: <span className="font-semibold capitalize text-blue-600">{currentPlan}</span>
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl border-2 p-6 flex flex-col ${
                plan.highlight ? "border-blue-600" : "border-gray-200"
              } ${currentPlan === plan.id ? "ring-2 ring-green-400" : ""}`}
            >
              {plan.highlight && (
                <div className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-full w-fit mb-3">
                  Most popular
                </div>
              )}
              <div className="font-bold text-lg">{plan.name}</div>
              <div className="text-3xl font-bold mt-1 mb-1">
                {plan.price}<span className="text-sm font-normal text-gray-500">/mo</span>
              </div>
              <ul className="mt-4 space-y-2 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="text-sm text-gray-600 flex items-center gap-2">
                    <CheckCircle size={14} className="text-green-500" /> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => !plan.disabled && currentPlan !== plan.id && handleUpgrade(plan.id)}
                disabled={plan.disabled || currentPlan === plan.id || loading === plan.id}
                className={`mt-6 py-2 rounded-lg text-sm font-medium transition ${
                  currentPlan === plan.id
                    ? "bg-green-100 text-green-700 cursor-default"
                    : plan.highlight
                    ? "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                    : "bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-60"
                }`}
              >
                {currentPlan === plan.id ? "✓ Active" : loading === plan.id ? "Processing..." : plan.cta}
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
