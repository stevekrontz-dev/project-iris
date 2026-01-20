"""
UGA NEUROSCIENCE FACULTY
Extracted from https://neuroscience.uga.edu/faculty/
"""

UGA_NEURO_FACULTY = [
    {"name": "Michael Bartlett", "position": "Georgia Athletic Association Professor", "department": "Pharmaceutical and Biomedical Sciences", "email": "mgbart@uga.edu", "research": "ADME of drugs; memory, cognition, neuropathic pain"},
    {"name": "Steven Beach", "position": "Distinguished Research Professor", "department": "Psychology", "email": "srhbeach@uga.edu", "research": "Epigenetics, marital processes, depression, anxiety"},
    {"name": "Mark Brown", "position": "Professor", "department": "Entomology", "email": "mrbrown@uga.edu", "research": "Neuro-endocrinology of insects"},
    {"name": "Jarrod Call", "position": "Assistant Professor", "department": "Kinesiology", "email": "call@uga.edu", "research": "Skeletal muscle physiology, mitochondrial physiology, regenerative medicine"},
    {"name": "Paige Carmichael", "position": "Professor", "department": "Pathology", "email": "kpc@uga.edu", "research": "Inherited diseases, ophthalmic pathology"},
    {"name": "Brett Clementz", "position": "Professor, Director Bio-Imaging Research Center", "department": "Psychology", "email": "clementz@uga.edu", "research": "Structural, functional & genetic abnormalities in schizophrenia"},
    {"name": "Julie Coffield", "position": "Associate Professor", "department": "Toxicology", "email": "coffield@uga.edu", "research": "Neurotoxicology, Botulinum neurotoxins"},
    {"name": "Brian Condie", "position": "Associate Professor", "department": "Genetics", "email": "bcondie@uga.edu", "research": "Mouse pharyngeal development, chromosome engineering"},
    {"name": "Brian Cummings", "position": "Professor, Director Interdisciplinary Toxicology Program", "department": "Pharmaceutical and Biomedical Sciences", "email": "bsc@rx.uga.edu", "research": "Molecular toxicology, cell signaling, prostate cancer"},
    {"name": "Krzysztof Czaja", "position": "Associate Professor", "department": "Veterinary Biosciences", "email": "czajak@uga.edu", "research": ""},
    {"name": "Steve Dalton", "position": "Professor, GRA Eminent Scholar", "department": "Cellular Biology", "email": "sdalton@uga.edu", "research": "Stem cell biology, cell therapies for diabetes and cardiovascular disease"},
    {"name": "Claire de La Serre", "position": "Assistant Professor", "department": "Foods and Nutrition", "email": "cdlserre@uga.edu", "research": "Diet and energy balance, gut microbiota, gut-brain signaling"},
    {"name": "Rodney K. Dishman", "position": "Professor", "department": "Kinesiology", "email": "rdishman@uga.edu", "research": ""},
    {"name": "Gaylen L. Edwards", "position": "Department Head, Georgia Athletic Association Professor", "department": "Physiology & Pharmacology", "email": "gedwards@uga.edu", "research": "Neural processing of abdominal sensory information, ingestive behavior"},
    {"name": "Jonathan Eggenschwiler", "position": "Associate Professor", "department": "Genetics", "email": "jeggensc@uga.edu", "research": "Tissue patterning during mammalian embryonic development"},
    {"name": "Adviye Ergul", "position": "Regents' Professor, Co-Director Physiology Graduate Program", "department": "Physiology (Augusta University)", "email": "aergul@augusta.edu", "research": ""},
    {"name": "Susan Fagan", "position": "Distinguished Research Professor, Assistant Dean Augusta University", "department": "Clinical and Administrative Pharmacy", "email": "sfagan@augusta.edu", "research": "Stroke, experimental therapeutics, angiotensin modulation"},
    {"name": "Nikolay (Nick) M. Filipov", "position": "Professor", "department": "Physiology and Pharmacology", "email": "filipov@uga.edu", "research": "Neurotoxicology, neuroimmunology, basal ganglia disorders"},
    {"name": "Dorothy Munkenbeck Fragaszy", "position": "Professor, Director Primate Behavior Laboratory", "department": "Psychology", "email": "doree@uga.edu", "research": "Primate behavior, problem-solving, skill learning in capuchin monkeys"},
    {"name": "James Franklin", "position": "Associate Professor", "department": "Pharmaceutical and Biomedical Sciences", "email": "jfrankli@rx.uga.edu", "research": "Neuronal apoptosis, mitochondria, Alzheimer's disease"},
    {"name": "Silvia Giraudo", "position": "Associate Professor", "department": "Foods and Nutrition", "email": "sgiraudo@uga.edu", "research": ""},
    {"name": "Phil Holmes", "position": "Professor, Neuroscience Program Chair", "department": "Psychology", "email": "pvholmes@uga.edu", "research": ""},
    {"name": "Daichi Kamiyama", "position": "Assistant Professor", "department": "Cellular Biology", "email": "daichi.kamiyama@uga.edu", "research": ""},
    {"name": "Lohitash Karumbaiah", "position": "Associate Professor, Regenerative Medicine", "department": "Regenerative Bioscience Center", "email": "lohitash@uga.edu", "research": "Regenerative medicine, neural engineering"},
    {"name": "William Kisaalita", "position": "Professor", "department": "Chemical, Materials, and Biomedical Engineering", "email": "williamk@engr.uga.edu", "research": ""},
    {"name": "Peter Kner", "position": "Associate Professor", "department": "Electrical and Computer Engineering", "email": "kner@engr.uga.edu", "research": ""},
    {"name": "James Lauderdale", "position": "Associate Professor, Graduate Coordinator Neuroscience", "department": "Cellular Biology", "email": "jdlauder@uga.edu", "research": ""},
    {"name": "Jae-Kyung Lee", "position": "Assistant Professor", "department": "Physiology and Pharmacology", "email": "jamlee@uga.edu", "research": ""},
    {"name": "Hongxiang Liu", "position": "Assistant Professor", "department": "Animal & Dairy Science", "email": "lhx@uga.edu", "research": ""},
    {"name": "Tianming Liu", "position": "Distinguished Research Professor", "department": "Computer Science", "email": "tliu@cs.uga.edu", "research": ""},
    {"name": "Jennifer McDowell", "position": "Professor & Chair", "department": "Psychology", "email": "jemcd@uga.edu", "research": "BioImaging Research"},
]


def get_uga_faculty():
    faculty = []
    for i, f in enumerate(UGA_NEURO_FACULTY):
        faculty.append({
            "id": f"uga-neuro-{i}",
            "name": f["name"],
            "institution": "University of Georgia",
            "institution_slug": "uga-neuro",
            "department": f["department"],
            "position": f["position"],
            "email": f["email"],
            "research_interests": f.get("research", ""),
            "profile_url": f"https://neuroscience.uga.edu/faculty/"
        })
    return faculty


if __name__ == '__main__':
    import json
    faculty = get_uga_faculty()
    print(f"UGA Neuroscience Faculty: {len(faculty)}")
    print(json.dumps(faculty[:3], indent=2))
