#!/usr/bin/env python3
"""
PrintHub Tenant Provisioning Utility
Creates a new tenant shop in Supabase:
1. Provisions Auth user in auth.users
2. Creates row in printhub_shops
3. Initializes default rates in printhub_settings
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

SUPABASE_URL = "https://mzkizzakuporgzljealz.supabase.co"

def request_json(url, method="GET", payload=None, headers=None):
    if headers is None:
        headers = {}
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get('message') or err_json.get('msg') or err_json.get('error_description') or err_body
        except Exception:
            msg = err_body
        raise RuntimeError(f"HTTP {e.code}: {msg}")

def main():
    print("=" * 60)
    print("   PRINTHUB - NEW SHOP PROVISIONING CONSOLE")
    print("=" * 60)

    # Need Service Role Key for provisioning Auth Users & bypassing tenant RLS
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not service_key:
        service_key = input("Enter Supabase Service Role Key: ").strip()
    if not service_key:
        print("[ERROR] Service Role Key is required to create tenant accounts.")
        sys.exit(1)

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    email = input("Shop Owner Email: ").strip()
    password = input("Shop Owner Password: ").strip()
    shop_name = input("Shop Name (e.g. Jagdalpur Xerox Center): ").strip()
    subdomain = input("Shop Subdomain Slug (e.g. jagdalpur): ").strip().lower()
    location = input("Shop Location (e.g. Bus Stand HQ): ").strip() or "HQ"
    
    days_str = input("Subscription Validity in Days [default: 30]: ").strip()
    days = int(days_str) if days_str.isdigit() else 30
    expiry_dt = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

    if not email or not password or not shop_name or not subdomain:
        print("[ERROR] Email, password, shop name, and subdomain are strictly mandatory.")
        sys.exit(1)

    print("\n[*] Provisioning Auth credentials...")
    user_id = None
    try:
        # Create user via Supabase Admin API
        user_res = request_json(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            method="POST",
            payload={"email": email, "password": password, "email_confirm": True},
            headers=headers
        )
        user_id = user_res.get("id")
        print(f"    [+] Auth User created: {user_id}")
    except RuntimeError as e:
        if "already registered" in str(e).lower() or "unique" in str(e).lower():
            print("    [!] User already exists. Fetching existing User ID...")
            users_list = request_json(
                f"{SUPABASE_URL}/auth/v1/admin/users?per_page=1000",
                headers=headers
            )
            for u in users_list.get("users", []):
                if u.get("email") == email:
                    user_id = u.get("id")
                    break
            if not user_id:
                print(f"[ERROR] Could not resolve existing user: {e}")
                sys.exit(1)
            print(f"    [+] Resolved User ID: {user_id}")
        else:
            print(f"[ERROR] Failed to create auth user: {e}")
            sys.exit(1)

    print("[*] Creating shop record in printhub_shops...")
    shop_payload = {
        "owner_uid": user_id,
        "shop_name": shop_name,
        "subdomain": subdomain,
        "location": location,
        "is_active": True,
        "subscription_expiry": expiry_dt
    }
    
    try:
        shop_res = request_json(
            f"{SUPABASE_URL}/rest/v1/printhub_shops",
            method="POST",
            payload=shop_payload,
            headers=headers
        )
        created_shop = shop_res[0] if isinstance(shop_res, list) and shop_res else shop_res
        shop_id = created_shop.get("id")
        print(f"    [+] Shop registered with ID: {shop_id}")
    except RuntimeError as e:
        print(f"[ERROR] Failed to insert shop: {e}")
        sys.exit(1)

    print("[*] Initializing default pricing in printhub_settings...")
    settings_payload = {
        "shop_id": shop_id,
        "price_bw": 2.0,
        "price_color": 10.0,
        "offer_banner": ""
    }
    try:
        request_json(
            f"{SUPABASE_URL}/rest/v1/printhub_settings",
            method="POST",
            payload=settings_payload,
            headers=headers
        )
        print("    [+] Default rates applied (B&W: ₹2.00, Color: ₹10.00).")
    except RuntimeError as e:
        print(f"[WARN] Failed to insert default settings: {e}")

    print("\n" + "=" * 60)
    print("   TENANT PROVISIONED SUCCESSFULLY!")
    print("=" * 60)
    print(f"  Shop Name    : {shop_name}")
    print(f"  Shop ID      : {shop_id}")
    print(f"  Subdomain    : {subdomain}")
    print(f"  Login Email  : {email}")
    print(f"  Expiry Date  : {expiry_dt}")
    print("-" * 60)
    print(f"  Customer URL : https://printhub-hybrid-pi.vercel.app/?shop={subdomain}")
    print(f"  Agent Portal : https://printhub-hybrid-pi.vercel.app/dashboard.html")
    print(f"  Print Bridge : Run print_bridge.py with email & password")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
