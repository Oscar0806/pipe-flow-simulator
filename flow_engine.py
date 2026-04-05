import numpy as np
from scipy.optimize import fsolve
 
PIPE_MATERIALS = {
    "Drawn Copper": 0.0015, "Commercial Steel": 0.045,
    "Galvanized Iron": 0.15, "Cast Iron": 0.26,
    "Concrete": 1.0, "Riveted Steel": 3.0, "PVC / Plastic": 0.0015,
}
 
PIPE_FLUIDS = {
    "Water (20°C)": {"rho":998,"mu":0.001003,"nu":1.004e-6},
    "Water (80°C)": {"rho":972,"mu":0.000355,"nu":3.65e-7},
    "Air (20°C, 1atm)": {"rho":1.204,"mu":1.825e-5,"nu":1.516e-5},
    "Engine Oil (40°C)": {"rho":876,"mu":0.0326,"nu":3.72e-5},
    "Glycerin (25°C)": {"rho":1261,"mu":0.95,"nu":7.53e-4},
}
 
def colebrook(Re, eps_D):
    """Solve Colebrook-White equation for Darcy friction factor."""
    if Re < 2300:
        return 64 / max(Re, 1)
    def eq(f):
        return 1/np.sqrt(f) + 2*np.log10(eps_D/3.7 + 2.51/(Re*np.sqrt(f)))
    f_sol = fsolve(eq, 0.02, full_output=False)[0]
    return max(f_sol, 1e-6)
 
def velocity_profile(R, r_pts, Re):
    """Laminar (parabolic) or turbulent (1/7th power law) profile."""
    if Re < 2300:
        return 2 * (1 - (r_pts/R)**2)  # Normalized to V_mean=1
    else:
        n = 7
        v_center = (n+1)*(2*n+1)/(2*n**2)
        return v_center * np.maximum(1 - np.abs(r_pts)/R, 0)**(1/n)
 
def analyze_pipe(fluid_name, material, D_mm, L_m, Q_m3h, fittings=None):
    """Complete pipe flow analysis."""
    fluid = PIPE_FLUIDS[fluid_name]
    eps = PIPE_MATERIALS[material]
    D = D_mm / 1000
    A = np.pi * (D/2)**2
    Q = Q_m3h / 3600
    V = Q / A
    Re = fluid["rho"] * V * D / fluid["mu"]
    eps_D = (eps/1000) / D
    f = colebrook(Re, eps_D)
    dp_friction = f * (L_m/D) * 0.5 * fluid["rho"] * V**2
    h_friction = dp_friction / (fluid["rho"] * 9.81)
 
    K_VALUES = {"90° elbow":0.9,"45° elbow":0.4,"Tee (branch)":1.8,
        "Gate valve (open)":0.2,"Globe valve (open)":10.0,
        "Check valve":2.5,"Sharp entry":0.5,"Exit":1.0}
    K_total = 0
    fitting_details = []
    if fittings:
        for name, count in fittings.items():
            k = K_VALUES.get(name, 0.5)
            K_total += k * count
            fitting_details.append({"fitting":name,"K":k,"count":count,"K_total":k*count})
 
    dp_minor = K_total * 0.5 * fluid["rho"] * V**2
    h_minor = dp_minor / (fluid["rho"] * 9.81)
    dp_total = dp_friction + dp_minor
    h_total = h_friction + h_minor
    P_pump = dp_total * Q
    R = D/2
    r = np.linspace(-R, R, 100)
    v_prof = velocity_profile(R, r, Re) * V
    regime = "Laminar" if Re<2300 else "Transitional" if Re<4000 else "Turbulent"
 
    return {"fluid":fluid_name,"material":material,"D_mm":D_mm,"L_m":L_m,
        "Q_m3h":Q_m3h,"V_m_s":round(V,3),"Re":round(Re,0),"regime":regime,
        "f_darcy":round(f,6),"eps_D":round(eps_D,6),
        "dp_friction_Pa":round(dp_friction,1),"dp_minor_Pa":round(dp_minor,1),
        "dp_total_Pa":round(dp_total,1),"dp_total_bar":round(dp_total/1e5,4),
        "h_friction_m":round(h_friction,3),"h_minor_m":round(h_minor,3),
        "h_total_m":round(h_total,3),"P_pump_W":round(P_pump,1),
        "r_profile":r,"v_profile":v_prof,"fitting_details":fitting_details}
 
def moody_chart_data():
    Re_range = np.logspace(2.5, 7, 200)
    eps_D_values = [0,1e-6,1e-5,5e-5,1e-4,5e-4,1e-3,5e-3,1e-2,5e-2]
    data = {}
    for ed in eps_D_values:
        data[ed] = [colebrook(Re, ed) for Re in Re_range]
    return Re_range, data
 
if __name__ == "__main__":
    r = analyze_pipe("Water (20°C)","Commercial Steel",50,100,10.0,
                      {"90° elbow":4,"Gate valve (open)":2,"Sharp entry":1,"Exit":1})
    print("═"*50)
    print("  PIPE FLOW ANALYSIS RESULTS")
    print("═"*50)
    for k,v in r.items():
        if k not in ("r_profile","v_profile","fitting_details"):
            print(f"  {k:20s}: {v}")
