import sys
sys.path.insert(0, '.')

print("Importing web_dashboard module...")
import web_dashboard

print(f"\nTotal routes in app: {len(web_dashboard.app.routes)}")
print("\nAll routes:")
for route in web_dashboard.app.routes:
    if hasattr(route, 'path'):
        methods = list(route.methods) if hasattr(route, 'methods') else []
        print(f"  {route.path:50} {methods}")

swarm_routes = [r for r in web_dashboard.app.routes if hasattr(r, 'path') and 'swarm' in r.path]
print(f"\nSwarm routes found: {len(swarm_routes)}")
for route in swarm_routes:
    print(f"  {route.path}")

print("\nChecking PantheonSwarm availability:")
print(f"  PantheonSwarm class: {web_dashboard.PantheonSwarm}")
print(f"  Dashboard swarm instance: {web_dashboard.dashboard.swarm if hasattr(web_dashboard.dashboard, 'swarm') else 'N/A'}")
