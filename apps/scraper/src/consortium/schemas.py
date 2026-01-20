"""
ATLANTA CONSORTIUM FACULTY SCRAPER
===================================
Complete schema mapping for each institution, then university-wide deployment.

PHASE 1: Schema Discovery & Validation
PHASE 2: University-Wide Swarm Deployment
"""

# ============================================================================
# INSTITUTION SCHEMAS - How to extract faculty data from each source
# ============================================================================

INSTITUTION_SCHEMAS = {
    
    # -------------------------------------------------------------------------
    # GEORGIA STATE UNIVERSITY - Neuroscience Institute
    # -------------------------------------------------------------------------
    'gsu_neuroscience': {
        'name': 'GSU Neuroscience Institute',
        'index_url': 'https://neuroscience.gsu.edu/directory/',
        'extraction_method': 'text_content',  # Use thalamus_get_text
        'profile_pattern': 'https://neuroscience.gsu.edu/profile/{slug}/',
        'faculty_count': 87,  # Validated
        'schema': {
            'name': {'pattern': r'^([A-Z][a-zA-Z\'\-]+),\s+([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]*)?)$', 'block_type': 'p'},
            'department': {'follows_name': True, 'block_type': 'p', 'contains': ['Neuroscience', 'Psychology', 'Biology']},
            'position': {'block_type': 'div', 'contains': ['professor', 'director', 'chair']},
            'email': {'pattern': r'[\w.-]+@gsu\.edu'},
            'research': {'block_type': 'p', 'min_length': 50},
        },
        'sample_faculty': [
            {'name': 'Aharoni, Eyal', 'department': 'Neuroscience, Philosophy, Psychology'},
            {'name': 'Albers, H Elliott', 'position': 'Regents Professor of Neuroscience'},
            {'name': 'Calhoun, Vince', 'position': 'Distinguished University Professor'},
        ]
    },
    
    # -------------------------------------------------------------------------
    # EMORY UNIVERSITY - School of Medicine Neurology
    # -------------------------------------------------------------------------
    'emory_neurology': {
        'name': 'Emory Neurology',
        'index_url': 'https://med.emory.edu/departments/neurology/faculty-and-research/index.html',
        'extraction_method': 'text_content',  # Similar to GSU
        'profile_pattern': 'https://med.emory.edu/directory/profile/?u={id}',
        'faculty_count': 86,  # Validated
        'schema': {
            'name': {'pattern': r'^([A-Z][a-zA-Z\'\-]+),\s+([A-Z][a-zA-Z\'\-]+)', 'block_type': 'p'},
            'department': {'follows_name': True, 'block_type': 'p'},
            'position': {'block_type': 'div', 'contains': ['professor', 'director', 'chair']},
            'email': {'pattern': r'[\w.-]+@emory\.edu'},
        },
        'notes': 'Uses GSU directory format (shared page?), validate actual Emory faculty'
    },
    
    # -------------------------------------------------------------------------
    # GEORGIA TECH - Coulter BME Department
    # -------------------------------------------------------------------------
    'gatech_bme': {
        'name': 'Georgia Tech Biomedical Engineering',
        'index_url': 'https://bme.gatech.edu/our-people/our-faculty',
        'extraction_method': 'web_fetch_profiles',  # JS-rendered index, fetch individual profiles
        'profile_pattern': 'https://bme.gatech.edu/bio/{slug}',
        'faculty_count': 90,  # Per index page "Results: 1 - 24 of 90"
        'platform': 'Drupal 10',
        'schema': {
            'name': {'selector': 'h1', 'transform': 'title_case'},
            'position': {'follows': 'Title/Position', 'block_type': 'text'},
            'research_areas': {'selector': '/research/areas-research/', 'type': 'links'},
            'publications': {'pattern': r'scholar\.google\.com/citations[^"]+'},
            'contact': {
                'phone': {'pattern': r'\d{3}\.\d{3}\.\d{4}'},
                'email': {'pattern': r'[\w.-]+@(?:gatech|emory)\.edu'},
                'office': {'follows': 'Contact', 'block_type': 'text'},
            },
            'lab': {'pattern': r'\[([^\]]+Lab(?:oratory)?)\]'},
        },
        'sample_faculty': [
            {
                'name': 'Lakshmi (Prasad) Dasi',
                'position': 'Rozelle Vanda Wesley Professor', 
                'research_areas': ['Biomaterials & Regenerative Technologies', 'Cardiovascular Engineering'],
                'phone': '404.385.1265',
                'lab': 'Cardiovascular Fluid Mechanics Laboratory',
                'google_scholar': 'https://scholar.google.com/citations?hl=en&user=CC7aZdcAAAAJ'
            },
            {
                'name': 'Jaydev P. Desai',
                'position': 'Cardiovascular Biomedical Engineering Distinguished Chair',
                'research_areas': ['Medical Robotics', 'Neuroengineering'],
            }
        ]
    },
}

# ============================================================================
# UNIVERSITY-WIDE EXPANSION TARGETS
# ============================================================================

UNIVERSITY_EXPANSION = {
    'georgia_tech': {
        'total_faculty_estimate': 1100,
        'colleges': [
            {'name': 'College of Engineering', 'url': 'https://coe.gatech.edu/', 'departments': [
                'Biomedical Engineering',  # Already have schema
                'Electrical & Computer Engineering',
                'Mechanical Engineering', 
                'Chemical & Biomolecular Engineering',
                'Materials Science & Engineering',
                'Aerospace Engineering',
                'Civil & Environmental Engineering',
            ]},
            {'name': 'College of Computing', 'url': 'https://cc.gatech.edu/', 'departments': [
                'Computer Science',
                'Computational Science & Engineering',
                'Interactive Computing',
            ]},
            {'name': 'College of Sciences', 'url': 'https://cos.gatech.edu/', 'departments': [
                'Physics',
                'Chemistry & Biochemistry',
                'Mathematics',
                'Biology',
                'Psychology',
            ]},
        ]
    },
    'emory': {
        'total_faculty_estimate': 3500,
        'schools': [
            {'name': 'School of Medicine', 'url': 'https://med.emory.edu/', 'departments': [
                'Neurology',  # Already have schema
                'Psychiatry',
                'Radiology',
                'Surgery',
                'Biomedical Informatics',
            ]},
            {'name': 'Rollins School of Public Health', 'url': 'https://sph.emory.edu/'},
            {'name': 'College of Arts & Sciences', 'url': 'https://college.emory.edu/'},
        ]
    },
    'georgia_state': {
        'total_faculty_estimate': 1800,
        'colleges': [
            {'name': 'College of Arts & Sciences', 'url': 'https://cas.gsu.edu/', 'departments': [
                'Neuroscience Institute',  # Already have schema
                'Psychology',
                'Biology',
                'Chemistry',
                'Physics & Astronomy',
                'Computer Science',
            ]},
            {'name': 'J. Mack Robinson College of Business', 'url': 'https://robinson.gsu.edu/'},
            {'name': 'Andrew Young School of Policy Studies', 'url': 'https://aysps.gsu.edu/'},
        ]
    },
}

print("=" * 70)
print("ATLANTA CONSORTIUM - INSTITUTION SCHEMAS")
print("=" * 70)
for key, schema in INSTITUTION_SCHEMAS.items():
    print(f"\n{schema['name']}")
    print(f"  Index: {schema['index_url']}")
    print(f"  Method: {schema['extraction_method']}")
    print(f"  Faculty Count: {schema.get('faculty_count', 'Unknown')}")
    if 'sample_faculty' in schema:
        print(f"  Sample: {schema['sample_faculty'][0]['name']}")

print("\n" + "=" * 70)
print("UNIVERSITY-WIDE EXPANSION POTENTIAL")
print("=" * 70)
total = 0
for uni, data in UNIVERSITY_EXPANSION.items():
    print(f"\n{uni.upper()}: ~{data['total_faculty_estimate']} faculty")
    total += data['total_faculty_estimate']
print(f"\n>>> TOTAL POTENTIAL: ~{total} faculty across Atlanta consortium")
