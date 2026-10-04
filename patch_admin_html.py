with open("templates/admin.html", "r") as f:
    code = f.read()

# Insert alert banner at the top of the content block
alert_block = """{% block content %}
    {% if is_locked %}
    <div style="background: #dc3545; color: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; text-align: center; border: 4px solid #721c24; animation: pulse 2s infinite;">
        <h1 style="margin: 0 0 1rem 0; font-size: 2.5rem; text-transform: uppercase;">⚠️ FATAL SYSTEM LOCK ⚠️</h1>
        <p style="font-size: 1.2rem; font-weight: bold;">Your PrintHub SaaS Subscription has completely expired. The 3-day grace period is over.</p>
        <p>Please contact Akshay to renew your subscription and unlock the hardware agent. All print jobs are frozen.</p>
    </div>
    {% elif in_grace_period %}
    <div style="background: #ffc107; color: #856404; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; border: 3px solid #ffeeba; box-shadow: 0 4px 15px rgba(255, 193, 7, 0.4);">
        <h2 style="margin: 0 0 0.5rem 0; font-size: 1.8rem; text-transform: uppercase;">🚨 HIGH ALERT: SUBSCRIPTION EXPIRED 🚨</h2>
        <p style="font-size: 1.1rem; font-weight: bold; margin: 0;">You are currently operating in the 3-day emergency grace period.</p>
        <p style="margin: 0.5rem 0 0 0;">Pay your platform rent immediately. If payment is not received, this software will lock automatically, and you will lose access to all pending orders.</p>
    </div>
    {% else %}
    <div style="background: #d4edda; color: #155724; padding: 0.75rem; border-radius: 4px; margin-bottom: 1.5rem; font-size: 0.9rem; border: 1px solid #c3e6cb; display: flex; justify-content: space-between; align-items: center;">
        <strong>Subscription Active</strong>
        <span>Expires in: {{ days_left }} days</span>
    </div>
    {% endif %}

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">"""

code = code.replace("""{% block content %}
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">""", alert_block)

# If locked, hide the print buttons
code = code.replace("""{% if not order.otp_verified %}""", """{% if is_locked %}
        <div style="padding: 1rem; background: #f8d7da; color: #721c24; border-radius: 4px; font-weight: bold; text-align: center;">SYSTEM LOCKED - PAY SUBSCRIPTION TO UNLOCK ORDERS</div>
        {% elif not order.otp_verified %}""")

with open("templates/admin.html", "w") as f:
    f.write(code)
print("admin.html updated for massive expiry alerts!")
