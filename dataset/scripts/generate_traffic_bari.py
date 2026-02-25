"""
Generatore Dataset Traffico - Città di Bari
Approccio vettorizzato con numpy/pandas per performance ottimale.
Output: dataset/output/bari_traffic_simulated_22_25.csv

Uso:
  python dataset/scripts/generate_traffic_bari.py            # 1 mese (test)
  python dataset/scripts/generate_traffic_bari.py --full     # 2022-2025 completo
"""

import sys
import pandas as pd
import numpy as np
import os

# ── Config ───────────────────────────────────────────────────────────────────
SEED = 42
rng = np.random.default_rng(SEED)

FULL_MODE  = '--full' in sys.argv
START_DATE = '2022-01-01'
END_DATE   = '2022-01-31' if not FULL_MODE else '2025-12-31'

# ── Strade principali ────────────────────────────────────────────────────────
MAIN_STREETS = {
    'Via Sparano':             {'neighborhood': 'Murat',        'zone_type': 'Downtown',   'road_type': 'Local Road'},
    'Corso Vittorio Emanuele': {'neighborhood': 'Murat',        'zone_type': 'Downtown',   'road_type': 'Main Road'},
    'SS16 Tangenziale':        {'neighborhood': 'Poggiofranco', 'zone_type': 'Suburban',   'road_type': 'Highway'},
    'Viale Einaudi':           {'neighborhood': 'Carrassi',     'zone_type': 'Commercial', 'road_type': 'Main Road'},
    'Via Bruno Buozzi':        {'neighborhood': 'Stanic',       'zone_type': 'Industrial', 'road_type': 'Main Road'},
    'Lungomare Nazario Sauro': {'neighborhood': 'Madonnella',   'zone_type': 'Downtown',   'road_type': 'Main Road'},
}

# ── Mappa quartieri → zone_type ──────────────────────────────────────────────
NEIGHBORHOOD_ZONE_MAP = {
    'murat':                 'Downtown',
    's.nicola':              'Downtown',
    'bari vecchia':          'Downtown',
    'madonnella':            'Downtown',
    'libertà':               'Residential',
    'japigia':               'Residential',
    'torre a mare':          'Residential',
    'carrassi':              'Commercial',
    'poggiofranco':          'Suburban',
    'picone':                'Suburban',
    's. pasquale':           'Suburban',
    'stanic':                'Industrial',
    'marconi san girolamo':  'Industrial',
}

# ── FIX 3: classificazione road_type migliorata ──────────────────────────────
# Keyword per Highway (prima, più specifiche)
HIGHWAY_KEYWORDS   = ['tangenziale', 'ss16', 'ss ', 'autostrada', 'raccordo', 'statale']
# Keyword per Main Road
MAINROAD_KEYWORDS  = ['corso', 'viale', 'lungomare', 'circonvallazione', 'traversa']
# Tutto il resto → Local Road

def infer_zone_type(neighborhood: str) -> str:
    n = neighborhood.lower()
    for key, zt in NEIGHBORHOOD_ZONE_MAP.items():
        if key in n:
            return zt
    return 'Residential'

def infer_road_type(street_name: str) -> str:
    n = street_name.lower()
    if any(k in n for k in HIGHWAY_KEYWORDS):
        return 'Highway'
    if any(k in n for k in MAINROAD_KEYWORDS):
        return 'Main Road'
    return 'Local Road'

def infer_neighborhood_if_missing(ubicazione: str) -> str:
    """Se quartiere manca: inferisce da Ubicazione o default S.Nicola (strade piccole centro storico)."""
    if ubicazione and pd.notna(ubicazione):
        u = str(ubicazione).lower()
        if ("pier" in u and "eremita" in u) or "s.nicola" in u or "san nicola" in u:
            return "S.Nicola"
        if "bari vecchia" in u or "centro storico" in u:
            return "Bari Vecchia"
    return "S.Nicola"


def load_extra_streets(csv_path: str) -> dict:
    """Carica strade da CSV (vie bari o vie_bari_arricchite). Usa lunghezza_m se presente."""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]

    extra = {}
    for _, row in df.iterrows():
        street = str(row.get('Odonimo', '')).strip().split('(')[0].strip()
        neighborhood = str(row.get('Quartiere (Località)', '')).strip().split(',')[0].strip()
        if neighborhood.lower() == 'nan' or not neighborhood:
            neighborhood = infer_neighborhood_if_missing(row.get('Ubicazione'))
        if not street or street == 'nan' or street in MAIN_STREETS:
            continue
        lung_m = row.get('lunghezza_m')
        lunghezza_m = None
        if pd.notna(lung_m) and str(lung_m).strip():
            try:
                lunghezza_m = float(lung_m)
            except (ValueError, TypeError):
                pass
        extra[street] = {
            'neighborhood': neighborhood,
            'zone_type':    infer_zone_type(neighborhood),
            'road_type':    infer_road_type(street),
            'lunghezza_m':  lunghezza_m,
        }
    return extra

# ── Logica vettorizzata ───────────────────────────────────────────────────────

ROAD_BASE_VOLUME = {'Highway': 5000.0, 'Main Road': 2000.0, 'Local Road': 1000.0}

# FIX 2: range velocità base per road_type + zone_type
ROAD_SPEED_RANGE = {
    # (min base, max base) in km/h — varieranno per congestione e meteo
    ('Highway',    'Suburban'):    (90.0, 130.0),
    ('Highway',    'Industrial'):  (80.0, 120.0),
    ('Highway',    'Residential'): (80.0, 120.0),
    ('Main Road',  'Downtown'):    (25.0,  55.0),
    ('Main Road',  'Commercial'):  (30.0,  60.0),
    ('Main Road',  'Residential'): (35.0,  65.0),
    ('Main Road',  'Suburban'):    (40.0,  70.0),
    ('Main Road',  'Industrial'):  (40.0,  70.0),
    ('Local Road', 'Downtown'):    (10.0,  30.0),   # centro storico = lento
    ('Local Road', 'Commercial'):  (15.0,  35.0),
    ('Local Road', 'Residential'): (20.0,  45.0),
    ('Local Road', 'Suburban'):    (25.0,  50.0),
    ('Local Road', 'Industrial'):  (20.0,  45.0),
}

# FIX 1+2: distanza con rumore per strada (diversa per ogni riga)
ROAD_BASE_DISTANCE = {'Highway': 10.0, 'Main Road': 5.0, 'Local Road': 2.5}

def sinusoidal_factor(hours: np.ndarray) -> np.ndarray:
    """Doppio picco: 08:00 (mattina) e 18:00 (sera)."""
    morning = np.exp(-0.5 * ((hours - 8) / 2.5) ** 2)
    evening = np.exp(-0.5 * ((hours - 18) / 2.5) ** 2)
    combined = 0.6 * morning + 0.8 * evening
    return 0.05 + 0.95 * np.clip(combined, 0, 1.0)

def build_street_df(street: str, meta: dict, timestamps: pd.DatetimeIndex, rng: np.random.Generator) -> pd.DataFrame:
    """Genera il DataFrame per una singola strada — tutto vettorizzato."""
    n          = len(timestamps)
    road_type  = meta['road_type']
    zone_type  = meta['zone_type']
    neighborhood = meta['neighborhood']
    base_vol   = ROAD_BASE_VOLUME[road_type]
    # Usa lunghezza reale da stradario se disponibile, altrimenti fallback
    lung_m = meta.get('lunghezza_m')
    if lung_m is not None and lung_m > 0:
        base_dist = lung_m / 1000.0  # metri → km
    else:
        base_dist = ROAD_BASE_DISTANCE[road_type]

    hours      = timestamps.hour.to_numpy()
    dow        = timestamps.dayofweek.to_numpy()
    is_weekend = dow >= 5

    # Meteo vettorizzato
    weather_idx = rng.choice(3, size=n, p=[0.70, 0.20, 0.10])
    weather_arr = np.array(['Clear', 'Rain', 'Fog'])
    weather     = weather_arr[weather_idx]

    is_rain = weather_idx == 1
    is_fog  = weather_idx == 2

    # is_event: 5% probabilità nelle ore 18-23
    evening_mask = (hours >= 18) & (hours <= 23)
    is_event     = np.zeros(n, dtype=bool)
    is_event[evening_mask] = rng.random(evening_mask.sum()) < 0.05

    # ── Volume ──────────────────────────────────────────────────────────────
    h_factor = sinusoidal_factor(hours)

    wk_morning   = is_weekend & (hours >= 7) & (hours <= 10)
    wk_afternoon = is_weekend & (hours >= 11) & (hours <= 16)
    h_factor = np.where(wk_morning,   h_factor * 0.60, h_factor)
    h_factor = np.where(wk_afternoon, h_factor * 1.15, h_factor)

    # Rumore organico per singola ora e strada (±15%)
    noise  = rng.uniform(0.85, 1.15, size=n)
    volume = base_vol * h_factor * noise

    # ── Modificatori pioggia (fascia oraria) ────────────────────────────────
    rain_mod = np.ones(n)
    masks_rain = [
        ((hours >= 6)  & (hours <= 9),  1.25, 1.45),   # mattina - pendolari
        ((hours >= 10) & (hours <= 12), 1.05, 1.15),   # metà mattina
        ((hours >= 13) & (hours <= 16), 1.10, 1.20),   # pomeriggio
        ((hours >= 17) & (hours <= 20), 1.30, 1.55),   # sera - effetto valanga
    ]
    covered_rain = np.zeros(n, dtype=bool)
    for mask_h, lo, hi in masks_rain:
        m = is_rain & mask_h
        if m.any():
            rain_mod[m] = rng.uniform(lo, hi, m.sum())
            covered_rain |= m
    # notte: gente resta a casa
    night_rain = is_rain & ~covered_rain
    if night_rain.any():
        rain_mod[night_rain] = rng.uniform(0.70, 0.85, night_rain.sum())

    # ── Modificatori nebbia ─────────────────────────────────────────────────
    fog_mod = np.ones(n)
    fog_0510 = is_fog & (hours >= 5) & (hours <= 10)
    fog_1117 = is_fog & (hours >= 11) & (hours <= 17)
    fog_night = is_fog & ~(fog_0510 | fog_1117)
    if fog_0510.any(): fog_mod[fog_0510] = rng.uniform(1.10, 1.25, fog_0510.sum())
    if fog_1117.any(): fog_mod[fog_1117] = rng.uniform(1.05, 1.15, fog_1117.sum())
    if fog_night.any(): fog_mod[fog_night] = rng.uniform(0.90, 1.10, fog_night.sum())

    volume = volume * rain_mod * fog_mod

    # Evento su strade principali: +80%
    if road_type in ('Main Road', 'Highway'):
        volume = np.where(is_event, volume * 1.80, volume)

    volume = np.clip(volume, 10, None).astype(int)

    # ── Congestion level ────────────────────────────────────────────────────
    t = {'Highway': (3000, 5000, 7000), 'Main Road': (1200, 2000, 2800), 'Local Road': (600, 1000, 1400)}[road_type]
    cong = np.full(n, 'Low', dtype=object)
    cong[volume >= t[0]] = 'Medium'
    cong[volume >= t[1]] = 'High'
    cong[volume >= t[2]] = 'Critical'
    if road_type in ('Main Road', 'Highway'):
        cong[is_event] = 'Critical'

    # ── FIX 2: Velocità per road_type + zone_type con range specifico ───────
    speed_range = ROAD_SPEED_RANGE.get((road_type, zone_type), (20.0, 50.0))
    # Velocità base randomizzata per ogni ora (distribuita nel range)
    speed = rng.uniform(speed_range[0], speed_range[1], size=n)

    # Meteo: riduzione velocità nelle fasce critiche
    if is_rain.any():
        rain_peak = is_rain & ((hours >= 6) & (hours <= 9) | (hours >= 17) & (hours <= 20))
        rain_off  = is_rain & ~rain_peak
        speed[rain_peak] *= rng.uniform(0.58, 0.72, rain_peak.sum()) if rain_peak.any() else 1
        speed[rain_off]  *= rng.uniform(0.75, 0.88, rain_off.sum())  if rain_off.any()  else 1
    if is_fog.any():
        speed[is_fog] *= rng.uniform(0.65, 0.78, is_fog.sum())

    # Congestione abbassa la velocità
    cong_factor = np.where(cong=='Critical', rng.uniform(0.25, 0.35, n),
                  np.where(cong=='High',     rng.uniform(0.45, 0.55, n),
                  np.where(cong=='Medium',   rng.uniform(0.70, 0.80, n), 1.0)))
    speed *= cong_factor
    speed = np.clip(speed, 3.0, None).round(1)

    # ── FIX 1: Travel time con distanza rumorosa per riga ───────────────────
    # Ogni riga ha un "tratto percorso" leggermente diverso (±25% della distanza base)
    dist_noise  = rng.uniform(0.75, 1.25, size=n)
    distance_km = base_dist * dist_noise
    travel_time = np.round((distance_km / np.maximum(speed, 1.0)) * 60, 1)

    # ── Incidenti ────────────────────────────────────────────────────────────
    acc_prob = np.where(
        is_rain & np.isin(cong, ['High', 'Critical']), rng.uniform(0.03, 0.06, n),
        np.where(is_fog  & np.isin(cong, ['High', 'Critical']), rng.uniform(0.02, 0.04, n),
        np.where(cong == 'Critical', 0.01, 0.0))
    )
    accident = np.where(rng.random(n) < acc_prob, 'Yes', 'No')

    return pd.DataFrame({
        'timestamp':           timestamps,
        'street_name':         street,
        'neighborhood':        neighborhood,
        'zone_type':           zone_type,
        'road_type':           road_type,
        'weather':             weather,
        'is_event':            is_event,
        'traffic_volume':      volume,
        'average_speed_kmph':  speed,
        'travel_time_minutes': travel_time,
        'congestion_level':    cong,
        'accident_reported':   accident,
    })

# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_root = os.path.dirname(script_dir)
    vie_arricchite = os.path.join(dataset_root, 'processed', 'vie_bari_arricchite.csv')
    vie_csv        = os.path.join(dataset_root, 'sources', 'vie_bari.csv')
    output_csv     = os.path.join(dataset_root, 'output', 'bari_traffic_simulated_22_25.csv')

    mode_label = "FULL (2022-2025)" if FULL_MODE else "TEST - 1 mese (2022-01)"
    print(f"=== Generatore Traffico Bari | Modalità: {mode_label} ===\n")
    print(f"Periodo: {START_DATE} → {END_DATE}")

    all_streets = dict(MAIN_STREETS)
    csv_to_use = vie_arricchite if os.path.exists(vie_arricchite) else vie_csv
    if os.path.exists(csv_to_use):
        extra = load_extra_streets(csv_to_use)
        all_streets.update(extra)
        # Stampa distribuzione road_type caricata
        from collections import Counter
        rt_count = Counter(v['road_type'] for v in all_streets.values())
        print(f"Strade: {len(all_streets)} totali → Highway:{rt_count['Highway']} | Main Road:{rt_count['Main Road']} | Local Road:{rt_count['Local Road']}\n")
    else:
        print("[WARNING] processed/vie_bari_arricchite.csv e sources/vie_bari.csv non trovati. Uso solo le 6 strade principali.\n")

    timestamps = pd.date_range(start=START_DATE, end=END_DATE + ' 23:00:00', freq='h')
    n_righe = len(timestamps) * len(all_streets)
    print(f"Timestamp: {len(timestamps):,} ore × {len(all_streets)} strade = {n_righe:,} righe attese\n")
    print("Generazione in corso...")

    chunks = []
    for i, (street, meta) in enumerate(all_streets.items(), 1):
        print(f"  [{i:3d}/{len(all_streets)}] {street:<40} ({meta['road_type']}, {meta['zone_type']})")
        chunks.append(build_street_df(street, meta, timestamps, rng))

    print("\nAssemblaggio DataFrame finale...")
    df = pd.concat(chunks, ignore_index=True)

    print(f"Salvataggio → {output_csv}")
    df.to_csv(output_csv, index=False)

    print(f"\n✅ Completato!")
    print(f"   Righe totali         : {len(df):,}")
    print(f"   Valori unici volume  : {df['traffic_volume'].nunique():,}")
    print(f"   Valori unici speed   : {df['average_speed_kmph'].nunique():,}")
    print(f"   Valori unici travel  : {df['travel_time_minutes'].nunique():,}")
    print(f"\n--- Distribuzione road_type ---")
    print(df['road_type'].value_counts().to_string())
    print(f"\n--- Distribuzione congestion_level ---")
    print(df['congestion_level'].value_counts().to_string())
    print(f"\n--- Volume medio per ora (media globale) ---")
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    hourly = df.groupby('hour')['traffic_volume'].mean().round(0)
    for h, v in hourly.items():
        bar = '█' * int(v / 80)
        print(f"  {h:02d}:00  {v:6.0f}  {bar}")
    print(f"\n--- Effetto pioggia mattina 06-09 ---")
    r = df[(df['weather']=='Rain')  & df['hour'].between(6,9)]['traffic_volume'].mean()
    c = df[(df['weather']=='Clear') & df['hour'].between(6,9)]['traffic_volume'].mean()
    print(f"  Clear={c:.0f}  Rain={r:.0f}  delta=+{(r/c-1)*100:.1f}%")
    print(f"\n--- Speed range per road_type ---")
    print(df.groupby('road_type')['average_speed_kmph'].describe()[['min','mean','max']].round(1).to_string())

    if not FULL_MODE:
        print(f"\n[INFO] Test OK. Per il dataset completo 2022-2025:")
        print(f"       python dataset/scripts/generate_traffic_bari.py --full")
