"""
EMORY NEUROLOGY FACULTY PARSER
Parse the faculty list from web_fetch HTML
"""
import re
import json

# Faculty data extracted from Emory Neurology page
# Pattern: ## [Name, Credentials](url) Title
EMORY_NEURO_FACULTY = [
    {"name": "Pratibha Aia, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=PAIA"},
    {"name": "Feras Akbik, MD, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=FAKBIK"},
    {"name": "Casey Albin, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=CSWOODW"},
    {"name": "Aaron Anderson, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=AMANDE9"},
    {"name": "Eleni Antzoulatos, MD, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=EANTZOU"},
    {"name": "Paul Beach, DO, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=PABEACH"},
    {"name": "Samir Belagaje, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=SBELAGA"},
    {"name": "Karima Benameur, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=KBENAME"},
    {"name": "Nicolas A. Bianchi, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=NABIANC"},
    {"name": "Valerie Biousse, MD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=VBIOUSS"},
    {"name": "Donald Bliwise, PhD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=DBLIWIS"},
    {"name": "Gabriela Bou, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=GBOU"},
    {"name": "Beau Bruce, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=BBBRUCE"},
    {"name": "Cathrin Buetefisch, MD, PhD", "position": "Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=CBUETEF"},
    {"name": "Katie Bullinger, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=KBULLI2"},
    {"name": "Brian Cabaniss, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=BCABANI"},
    {"name": "Vince Calhoun, PhD", "position": "Professor and TReNDS Director", "profile": "https://med.emory.edu/directory/profile/?u=VCALHO2"},
    {"name": "Christopher Caughman, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=CCAUGHM"},
    {"name": "Julien Cavanagh, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=JJCAVAN"},
    {"name": "Nancy Collop, MD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=NCOLLOP"},
    {"name": "Andrés De León, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=AMDELEO"},
    {"name": "Annaelle Devergnas, PhD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=ADEVERG"},
    {"name": "Swapan Dholakia, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=SDHOLAK"},
    {"name": "Jaydevsinh Dolia, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=JDOLIA"},
    {"name": "Christine Doss Esper, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=CEDOSS"},
    {"name": "Daniel Drane, PhD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=DDRANE"},
    {"name": "Gregory Esper, MD, MBA", "position": "Professor, Vice-Chair for Clinical Affairs", "profile": "https://www.med.emory.edu/directory/profile/?u=GESPER"},
    {"name": "Marian Evatt, MD, MS", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=MEVATT"},
    {"name": "Stewart Factor, DO", "position": "Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=SFACTOR"},
    {"name": "Christina Fournier, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=CFOURNI"},
    {"name": "Michael Frankel, MD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=MFRANKE"},
    {"name": "Adriana Galvan, PhD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=AGALVAN"},
    {"name": "Rocio Garcia Santibanez, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=RCGARCI"},
    {"name": "Evan Gedzelman, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=EGEDZEL"},
    {"name": "Jane L. Gilmore, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=JGILMOR"},
    {"name": "Jonathan Glass, MD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=JGLAS03"},
    {"name": "Ezequiel Gleichgerrcht, MD, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=ELGLEIC"},
    {"name": "Felicia Goldstein, PhD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=FGOLDST"},
    {"name": "James Greene, MD, PhD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=JGGREEN"},
    {"name": "Olivia Groover, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=OGROOVE"},
    {"name": "Chadwick Hales, MD, PhD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=CMHALES"},
    {"name": "Casey Hall, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=CLHALL2"},
    {"name": "Taylor B. Harrison, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=THARRI4"},
    {"name": "Diogo Haussen, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=DHAUSSE"},
    {"name": "Jing He, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=JHE40"},
    {"name": "Lenora Higginbotham, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=LHIGGI2"},
    {"name": "Romy Hoque, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=RHOQUE"},
    {"name": "Lucas Felipe Bastos Horta, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=LFELIPE"},
    {"name": "Daniel Huddleston, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=DEHUDDL"},
    {"name": "Spencer Hutto, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=SHUTTO"},
    {"name": "Dinesh Jillella, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=DJILLEL"},
    {"name": "Hyder Jinnah, MD, PhD", "position": "Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=HJINNAH"},
    {"name": "Erik C. B. Johnson, MD, PhD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=EJOHN40"},
    {"name": "Prem Kandiah, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=PKANDIA"},
    {"name": "Ioannis Karakis, MD, PhD, MSc", "position": "Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=IKARAK2"},
    {"name": "Vita Kesner, MD, PhD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=VKESNER"},
    {"name": "Jaffar Khan, MD", "position": "Professor and Chair", "profile": "https://med.emory.edu/directory/profile/?u=JKHAN"},
    {"name": "Kyung Wha Kim, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=KKIM80"},
    {"name": "Jacqueline V. Kraft, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=JKRAFT2"},
    {"name": "James J. Lah, MD, PhD", "position": "Alice and Roy Richards Professor and Chair", "profile": "https://www.med.emory.edu/directory/profile/?u=JLAH"},
    {"name": "Neil Lava, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=NLAVA"},
    {"name": "Eric C. Lawson", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=ELAWSO6"},
    {"name": "Allan Levey, MD, PhD", "position": "Betty Gage Holland Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=ALEVEY"},
    {"name": "Bernardo Liberato, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=BBOAVEN"},
    {"name": "David W. Loring, PhD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=DLORING"},
    {"name": "Rebecca Matthews, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=REFASAN"},
    {"name": "Svjetlana Miocinovic, MD, PhD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=SMIOCIN"},
    {"name": "Fadi B. Nahab, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=FNAHAB"},
    {"name": "Digvijaya Navalkele, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=DNAVALK"},
    {"name": "Nancy Newman, MD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=OPHTNJN"},
    {"name": "Joe Nocera, PhD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=JNOCERA"},
    {"name": "Mahmoud Obideen, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=MOBIDE3"},
    {"name": "Stella Papa, MD", "position": "Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=SPAPA"},
    {"name": "Monica Parker, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=MPARKE2"},
    {"name": "Vishal Patel, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=VNPATE3"},
    {"name": "David Pearce, MD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=DPEARCE"},
    {"name": "Cederic M. Pimentel-Farias, MD", "position": "Assistant Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=CPIMENT"},
    {"name": "Sharon Polensek, MD, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=SSHARTM"},
    {"name": "Jonathan Ratcliff, MD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=JRATCLI"},
    {"name": "Amy Rodriguez, MD", "position": "Associate Professor", "profile": "https://med.emory.edu/directory/profile/?u=ARODR30"},
    {"name": "Andres Rodriguez-Ruiz, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=AARODR4"},
    {"name": "David Rye, MD, PhD", "position": "Professor", "profile": "https://med.emory.edu/directory/profile/?u=DRYE"},
    {"name": "Ofer Sadan, MD", "position": "Associate Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=OSADAN"},
    {"name": "Owen B. Samuels, MD", "position": "Professor", "profile": "https://www.med.emory.edu/directory/profile/?u=OBSAMUE"},
    {"name": "David S. Sandlin, MD, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=DSANDLI"},
    {"name": "Jessica Saurman, PhD", "position": "Assistant Professor", "profile": "https://med.emory.edu/directory/profile/?u=JSAURMA"},
]

# Convert to standard format
def get_emory_faculty():
    faculty = []
    for i, f in enumerate(EMORY_NEURO_FACULTY):
        faculty.append({
            "id": f"emory-neuro-{i}",
            "name": f["name"],
            "institution": "Emory University",
            "institution_slug": "emory-neuro",
            "department": "Neurology",
            "position": f["position"],
            "email": "",  # Would need to scrape profile pages
            "profile_url": f["profile"],
            "research_interests": ""
        })
    return faculty

if __name__ == '__main__':
    faculty = get_emory_faculty()
    print(f"Emory Neurology Faculty: {len(faculty)}")
    print(json.dumps(faculty[:3], indent=2))
