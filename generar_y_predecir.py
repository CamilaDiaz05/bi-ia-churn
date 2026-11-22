import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Generar datos simulados realistas de clientes (2,000 registros)
np.random.seed(42)
n = 2000

planes = np.random.choice(["Basic", "Pro", "Enterprise"], size=n, p=[0.5, 0.35, 0.15])
precio_plan = {"Basic": 19.0, "Pro": 49.0, "Enterprise": 129.0}

df = pd.DataFrame({
    "cliente_id": [f"CLI-{1000 + i}" for i in range(n)],
    "plan": planes,
    "ingreso_mensual": [precio_plan[p] for p in planes],
    "antiguedad_meses": np.random.randint(1, 36, size=n),
    "tickets_soporte_90d": np.random.poisson(lam=1.8, size=n),
    "dias_sin_uso": np.random.randint(0, 45, size=n),
})

# 2. Definir variable objetivo (fuga): más probable si hay muchos días sin uso,
#    muchos tickets y poca antigüedad
score_riesgo = (
    0.06 * df["dias_sin_uso"]
    + 0.35 * df["tickets_soporte_90d"]
    - 0.05 * df["antiguedad_meses"]
    - 1.5
)
prob_real = 1 / (1 + np.exp(-score_riesgo))
df["fuga_historica"] = (np.random.rand(n) < prob_real).astype(int)

# 3. Entrenar modelo de Machine Learning (Random Forest)
features = ["ingreso_mensual", "antiguedad_meses", "tickets_soporte_90d", "dias_sin_uso"]
X = pd.get_dummies(df[features + ["plan"]], columns=["plan"], drop_first=False)
y = df["fuga_historica"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

modelo = RandomForestClassifier(n_estimators=120, max_depth=7, random_state=42)
modelo.fit(X_train, y_train)

pred_test = modelo.predict(X_test)
precision = accuracy_score(y_test, pred_test)

# 4. Calcular probabilidad de fuga (0% a 100%) para todos los clientes
df["probabilidad_fuga"] = np.round(modelo.predict_proba(X)[:, 1] * 100, 1)

df["nivel_riesgo"] = np.where(
    df["probabilidad_fuga"] >= 70, "Alto",
    np.where(df["probabilidad_fuga"] >= 40, "Medio", "Bajo")
)

df["ingreso_en_riesgo"] = np.round(
    df["ingreso_mensual"] * (df["probabilidad_fuga"] / 100), 2
)

# Guardar dataset final para Power BI
df.to_csv("clientes_analitica_ia.csv", index=False)

# 5. Generar resumen ejecutivo automático (base para IA / reporte)
alto_riesgo = df[df["nivel_riesgo"] == "Alto"]
resumen = f"""
RESUMEN EJECUTIVO DE ANALÍTICA PREDICTIVA
- Precisión del modelo en prueba: {precision:.1%}
- Total de clientes analizados: {len(df)}
- Clientes en riesgo ALTO (>=70%): {len(alto_riesgo)} ({len(alto_riesgo)/len(df):.1%})
- Ingreso mensual estimado en riesgo (total ponderado): ${df['ingreso_en_riesgo'].sum():,.2f}
- Plan más expuesto en riesgo alto: {alto_riesgo['plan'].value_counts().idxmax() if len(alto_riesgo) > 0 else 'N/A'}
"""

with open("resumen_ia.txt", "w", encoding="utf-8") as f:
    f.write(resumen.strip())

print("Listo! Se generaron 'clientes_analitica_ia.csv' y 'resumen_ia.txt'.")
print(resumen)