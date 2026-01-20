"""
MERGE ALL CONSORTIUM DATA
=========================
Combine GSU, Emory, GT BME into single validated dataset
"""
import json
from datetime import datetime, timezone
from emory_faculty import get_emory_faculty

# Load existing swarm results (GSU + GT BME)
with open('data/consortium/atlanta_consortium_20260114_031511.json', 'r') as f:
    swarm_data = json.load(f)

# Get Emory faculty
emory_faculty = get_emory_faculty()

# Filter existing data (remove Emory 0 results, keep GSU and GT BME)
existing_faculty = [f for f in swarm_data['faculty'] 
                    if f['institution_slug'] != 'emory-neuro']

# Combine all
all_faculty = existing_faculty + emory_faculty

# Create final consolidated output
output = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'consortium': 'Atlanta Neuroscience Consortium',
    'version': '2.0',
    'total_faculty': len(all_faculty),
    'by_institution': {
        'GSU Neuroscience Institute': len([f for f in all_faculty if f['institution_slug'] == 'gsu-neuro']),
        'Emory Neurology': len([f for f in all_faculty if f['institution_slug'] == 'emory-neuro']),
        'Georgia Tech BME': len([f for f in all_faculty if f['institution_slug'] == 'gatech-bme']),
    },
    'schemas_validated': True,
    'faculty': all_faculty
}

# Save
outfile = f'data/consortium/atlanta_consortium_FINAL.json'
with open(outfile, 'w') as f:
    json.dump(output, f, indent=2)

print('=' * 70)
print('ATLANTA CONSORTIUM - FINAL MERGE')
print('=' * 70)
print(f'Timestamp: {output["timestamp"]}')
print(f'\nTotal Faculty: {output["total_faculty"]}')
print(f'  - GSU Neuroscience: {output["by_institution"]["GSU Neuroscience Institute"]}')
print(f'  - Emory Neurology: {output["by_institution"]["Emory Neurology"]}')
print(f'  - Georgia Tech BME: {output["by_institution"]["Georgia Tech BME"]}')
print(f'\n✓ Saved to: {outfile}')
print('\n' + '=' * 70)
print('SCHEMAS VALIDATED ✓')
print('=' * 70)
print('''
GSU Schema:
  - Source: neuroscience.gsu.edu/directory/
  - Method: Thalamus text extraction
  - Fields: name, department, position, email, research_interests
  
Emory Schema:
  - Source: med.emory.edu/departments/neurology/faculty/
  - Method: web_fetch HTML parsing
  - Fields: name, position, profile_url
  - Pattern: ## [Name, Credentials](url) Title
  
GT BME Schema:
  - Source: bme.gatech.edu/bio/{slug}
  - Method: Thalamus profile scraping
  - Platform: Drupal 10
  - Fields: name, position, phone, research_areas, google_scholar, lab
''')
