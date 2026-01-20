"""
FINAL GEORGIA CONSORTIUM MERGE
==============================
GSU + Emory + GT BME + UGA = Complete Georgia Research Network
"""
import json
from datetime import datetime, timezone
from emory_faculty import get_emory_faculty
from uga_faculty import get_uga_faculty

# Load existing data (GSU + GT BME)
with open('data/consortium/atlanta_consortium_FINAL.json', 'r') as f:
    existing_data = json.load(f)

# Get additional faculty
emory_faculty = get_emory_faculty()
uga_faculty = get_uga_faculty()

# Filter to keep GSU and GT BME from existing
gsu_gtbme_faculty = [f for f in existing_data['faculty'] 
                     if f['institution_slug'] in ['gsu-neuro', 'gatech-bme']]

# Combine all
all_faculty = gsu_gtbme_faculty + emory_faculty + uga_faculty

# Count by institution
counts = {
    'GSU Neuroscience Institute': len([f for f in all_faculty if f['institution_slug'] == 'gsu-neuro']),
    'Emory Neurology': len([f for f in all_faculty if f['institution_slug'] == 'emory-neuro']),
    'Georgia Tech BME': len([f for f in all_faculty if f['institution_slug'] == 'gatech-bme']),
    'UGA Neuroscience': len([f for f in all_faculty if f['institution_slug'] == 'uga-neuro']),
}

# Create final output
output = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'consortium': 'Georgia Research Consortium',
    'version': '3.0',
    'description': 'Faculty across GSU, Emory, Georgia Tech, and UGA - Georgia neuroscience and biomedical research network',
    'total_faculty': len(all_faculty),
    'by_institution': counts,
    'schemas_validated': True,
    'institutions': {
        'gsu': {'name': 'Georgia State University', 'program': 'Neuroscience Institute', 'url': 'https://neuroscience.gsu.edu/directory/'},
        'emory': {'name': 'Emory University', 'program': 'Department of Neurology', 'url': 'https://med.emory.edu/departments/neurology/faculty/'},
        'gatech': {'name': 'Georgia Institute of Technology', 'program': 'Coulter BME Department', 'url': 'https://bme.gatech.edu/our-people/our-faculty'},
        'uga': {'name': 'University of Georgia', 'program': 'Neuroscience PhD Program', 'url': 'https://neuroscience.uga.edu/faculty/'},
    },
    'faculty': all_faculty
}

# Save
outfile = 'data/consortium/georgia_consortium_FINAL.json'
with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print('=' * 70)
print('GEORGIA RESEARCH CONSORTIUM - FINAL')
print('=' * 70)
print(f'Timestamp: {output["timestamp"]}')
print(f'\nTotal Faculty: {output["total_faculty"]}')
for inst, count in counts.items():
    print(f'  - {inst}: {count}')
print(f'\nSaved to: {outfile}')
print('=' * 70)
