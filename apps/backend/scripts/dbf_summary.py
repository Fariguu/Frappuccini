"""
Script per analizzare i file DBF (Shapefile) nella cartella dataset.
Genera un report Markdown con schema e anteprima dati.
Esegui da apps/backend: python scripts/dbf_summary.py
"""

import datetime
import os
import struct
from pathlib import Path


def read_dbf_info(dbf_path: str) -> dict | None:
    """
    Legge info base e un campione di dati da un file DBF senza dipendenze esterne.
    """
    try:
        with open(dbf_path, 'rb') as f:
            # Header info
            header = f.read(32)
            if len(header) < 32:
                return None
            
            num_records = struct.unpack('<I', header[4:8])[0]
            header_len = struct.unpack('<H', header[8:10])[0]
            record_len = struct.unpack('<H', header[10:12])[0]
            
            # Field descriptors
            num_fields = (header_len - 33) // 32
            fields = []
            for _ in range(num_fields):
                field_data = f.read(32)
                if len(field_data) < 32:
                    break
                name = field_data[:11].decode('ascii').strip('\x00').strip()
                ftype = chr(field_data[11])
                flen = field_data[16]
                fields.append({'name': name, 'type': ftype, 'len': flen})
            
            # Read all records since there are only 5
            f.seek(header_len)
            sample_data = []
            for _ in range(num_records):
                record = f.read(record_len)
                if not record:
                    break
                # Skip deletion flag (1st byte)
                offset = 1
                row = {}
                for field in fields:
                    val = record[offset:offset+field['len']].decode('latin-1').strip()
                    row[field['name']] = val
                    offset += field['len']
                sample_data.append(row)
            
            return {
                'path': dbf_path,
                'records': num_records,
                'fields': fields,
                'sample': sample_data
            }
    except Exception as e:
        print(f"Error reading {dbf_path}: {e}")
        return None


def main() -> None:
    """Scansiona dataset/, trova file .dbf e genera report."""
    script_dir = Path(__file__).resolve().parent
    backend_root = script_dir.parent
    project_root = backend_root.parent

    dataset_dir = project_root / "dataset"
    if not dataset_dir.exists():
        dataset_dir = Path(os.getcwd()) / "dataset"
    if not dataset_dir.exists():
        print(f"Dataset directory not found at {dataset_dir}")
        return

    print(f"Scanning dataset at: {dataset_dir}")
    
    report = []
    report.append("# Dataset Summary Report")
    report.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("Ho analizzato i file nel folder `dataset` e ho estratto i metadati dai file Shapefile (.dbf).")
    report.append("")

    dbf_files = []
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.lower().endswith('.dbf'):
                dbf_files.append(os.path.join(root, file))

    if not dbf_files:
        report.append("Nessuna tabella (.dbf) trovata nella cartella dataset.")
    else:
        report.append(f"Trovate {len(dbf_files)} tabelle.")
        report.append("")
        
        for dbf_path in dbf_files:
            info = read_dbf_info(dbf_path)
            if info:
                rel_path = os.path.relpath(dbf_path, dataset_dir)
                report.append(f"## Tabella: `{rel_path}`")
                report.append(f"- **Record totali:** {info['records']}")
                report.append("- **Schema:**")
                report.append("  | Nome Campo | Tipo | Lunghezza |")
                report.append("  | :--- | :--- | :--- |")
                for field in info['fields']:
                    report.append(f"  | {field['name']} | {field['type']} | {field['len']} |")
                
                if info['sample']:
                    report.append("")
                    report.append("- **Anteprima dati (primi 3 record):**")
                    fields_to_show = [f['name'] for f in info['fields']]
                    header_row = "  | " + " | ".join(fields_to_show) + " |"
                    separator_row = "  | " + " | ".join([":---"] * len(fields_to_show)) + " |"
                    report.append(header_row)
                    report.append(separator_row)
                    for row in info['sample']:
                        data_row = "  | " + " | ".join([row.get(f, '') for f in fields_to_show]) + " |"
                        report.append(data_row)
                report.append("")

    report_path = script_dir / "dataset_report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"Report generato in: {report_path}")


if __name__ == "__main__":
    main()
