"use client";

import { useEffect, useState } from "react";
import Script from "next/script";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Invoice {
  id: string;
  invoice_number: string;
  total_paise: number;
  balance_paise: number;
  due_date: string;
  status: string;
  student: string;
}

export default function StudentDuesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const res = await fetch("/api/v1/payments/invoices/");
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.results || data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handlePayNow = async () => {
    setPaying(true);
    try {
      // 1. Get unpaid invoices
      const unpaid = invoices.filter(inv => inv.balance_paise > 0);
      if (unpaid.length === 0) return;
      
      const totalAmount = unpaid.reduce((sum, inv) => sum + inv.balance_paise, 0);
      const invoiceIds = unpaid.map(inv => inv.id);
      const studentId = unpaid[0].student; // Assuming all belong to same student for now
      
      // 2. Create order on backend
      const res = await fetch("/api/v1/payments/orders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount_paise: totalAmount,
          invoice_ids: invoiceIds,
          student_id: studentId
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        alert("Failed to create order: " + (err.error || "Unknown error"));
        return;
      }
      
      const order = await res.json();
      
      // 3. Initialize Razorpay
      const options = {
        key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_xxxx",
        amount: order.amount_paise,
        currency: "INR",
        name: "Perin Devi Natyalayam",
        description: "Fee Payment",
        order_id: order.razorpay_order_id,
        handler: async function (response: any) {
          // 4. Verify on backend (optional, but good for immediate UI update)
          const verifyRes = await fetch("/api/v1/payments/orders/confirm/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            })
          });
          
          if (verifyRes.ok) {
            alert("Payment Successful! Receipt is being generated.");
            fetchInvoices();
          } else {
            alert("Payment verification failed. Please contact admin if amount was deducted.");
          }
        },
        prefill: {
          name: "Student Name", // Should come from context
          email: "student@example.com",
          contact: "9999999999"
        },
        theme: {
          color: "#4f46e5"
        }
      };
      
      const rzp = new (window as any).Razorpay(options);
      rzp.on('payment.failed', function (response: any){
        alert("Payment Failed: " + response.error.description);
      });
      rzp.open();
      
    } catch (e) {
      console.error(e);
      alert("Something went wrong");
    } finally {
      setPaying(false);
    }
  };

  const unpaidInvoices = invoices.filter(inv => inv.balance_paise > 0);
  const totalDue = unpaidInvoices.reduce((sum, inv) => sum + inv.balance_paise, 0);

  if (loading) return <div>Loading dues...</div>;

  return (
    <div className="space-y-6">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" />
      
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Fee Dues</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{(totalDue / 100).toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              Across {unpaidInvoices.length} active invoices
            </p>
          </CardContent>
        </Card>
      </div>

      {unpaidInvoices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Pending Invoices</CardTitle>
            <CardDescription>Select invoices or pay all at once.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {unpaidInvoices.map(inv => (
                <div key={inv.id} className="flex justify-between items-center border p-4 rounded-md">
                  <div>
                    <p className="font-medium">{inv.invoice_number}</p>
                    <p className="text-sm text-muted-foreground">Due: {inv.due_date}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-red-600">₹{(inv.balance_paise / 100).toFixed(2)}</p>
                    <p className="text-sm text-muted-foreground">Total: ₹{(inv.total_paise / 100).toFixed(2)}</p>
                  </div>
                </div>
              ))}
              
              <div className="pt-4 flex justify-end">
                <Button onClick={handlePayNow} disabled={paying} size="lg">
                  {paying ? "Processing..." : `Pay ₹${(totalDue / 100).toFixed(2)} Now`}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {unpaidInvoices.length === 0 && (
        <div className="p-8 text-center border rounded-md bg-muted/20">
          <h3 className="text-lg font-medium">All clear!</h3>
          <p className="text-muted-foreground">You have no pending fee dues.</p>
        </div>
      )}
    </div>
  );
}
