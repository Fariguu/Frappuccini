# Dataset Bari - Traffico e Stradario

## Struttura

```
dataset/
├── scripts/              # Script Python
│   ├── generate_traffic_bari.py   # Genera dataset traffico simulato
│   ├── integrate_stradario_vie.py # Integra shapefile con vie bari
│   └── requirements.txt
├── sources/              # Dati sorgente
│   ├── vie_bari.csv      # Toponomastica Bari (Odonimo, Quartiere, Ubicazione)
│   ├── traffico.csv      # Dataset traffico generico
│   └── stradario/        # Shapefile stradario Bari
│       ├── Stradario.shp
│       ├── Stradario.dbf
│       ├── Stradario.shx
│       └── Stradario.prj
├── processed/            # Dati elaborati
│   └── vie_bari_arricchite.csv   # Vie bari + lunghezze da stradario
└── output/               # Output generati
    └── bari_traffic_simulated_22_25.csv
```

## Uso

**Integrare stradario con vie bari:**
```bash
pip install -r dataset/scripts/requirements.txt
python dataset/scripts/integrate_stradario_vie.py
```

**Generare traffico:**
```bash
python dataset/scripts/generate_traffic_bari.py        # 1 mese (test)
python dataset/scripts/generate_traffic_bari.py --full # 2022-2025
```
