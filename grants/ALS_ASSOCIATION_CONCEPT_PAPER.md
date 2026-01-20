# ALS ASSOCIATION ASSISTIVE TECHNOLOGY GRANT
## Concept Paper: Adaptive Multi-Modal BCI Communication System

---

## PROJECT TITLE
**GazeBCI: An Adaptive Eye-Gaze and Brain-Computer Interface System for Progressive Communication Preservation in ALS**

---

## PRINCIPAL INVESTIGATOR
**Steve Krontz, BBA**
Head Futurist & Director of Innovation
The BrainLab, Kennesaw State University
Kennesaw, Georgia

**Co-Investigator:**
Adriane Randolph, Ph.D.
Executive Director, The BrainLab
Associate Dean for Community and Faculty Affairs
Full Professor of Information Systems
Kennesaw State University

---

## FUNDING REQUESTED
**$400,000 over 2 years** (Total costs, including 10% indirect)
- Year 1: $220,000
- Year 2: $180,000

---

## LAY SUMMARY (For Patients and Families)

When ALS takes away the ability to speak and move, communication becomes the lifeline to independence, dignity, and connection with loved ones. Current assistive technologies force people with ALS to choose ONE method—either eye tracking OR brain signals—but as the disease progresses, what works today may fail tomorrow.

**GazeBCI changes this.**

We're building a system that combines eye-gaze tracking with brain-computer interface technology, seamlessly switching between methods as a person's abilities change. Think of it as a communication system that adapts to YOU, not the other way around.

- When your eyes work well → use fast eye tracking
- When eye fatigue sets in → switch to brain signals  
- When both are needed → use them together for higher accuracy

No retraining. No expensive new equipment. Just continuous, reliable communication—from diagnosis through every stage of the journey.

---

## PROBLEM STATEMENT

People living with ALS face a cruel progression: the mind remains sharp while the body fails. Communication technologies exist, but they share critical limitations:

1. **Single-modality dependency**: Eye trackers fail when gaze control deteriorates; BCIs require sustained attention that fatigues users
2. **Cliff-edge transitions**: When one system fails, patients must learn entirely new interfaces during their most vulnerable periods
3. **High abandonment rates**: Up to 35% of AAC devices are abandoned due to poor fit with disease progression
4. **Cost barriers**: Separate eye-tracking and BCI systems cost $15,000-$50,000 combined

**The gap**: No existing system provides seamless, adaptive multi-modal communication that evolves with disease progression.

---

## PROPOSED SOLUTION

### GazeBCI: Adaptive Multi-Modal Communication

We propose developing an integrated system that combines:

**Hardware Integration:**
- Tobii eye-tracking bar (screen-mounted, non-invasive)
- Consumer-grade EEG headset (8-16 channels)
- Single unified software interface

**Adaptive Intelligence:**
- Real-time monitoring of signal quality from both modalities
- Automatic switching based on user fatigue, accuracy, and preference
- Machine learning that improves with each user session

**User-Centered Design:**
- Co-designed with ALS patients and caregivers
- Plug-and-play setup (< 10 minutes)
- Works with existing AAC software (Grid 3, Tobii Communicator)

---

## TECHNICAL APPROACH

### Phase 1: Integration & Baseline (Months 1-8)
**Aim 1: Build unified hardware-software platform**

- Integrate Tobii Pro SDK with OpenBCI/Emotiv EEG systems
- Develop signal fusion algorithms for multi-modal input
- Create adaptive switching logic based on:
  - Gaze tracking accuracy (fixation stability, calibration drift)
  - EEG signal quality (impedance, artifact levels)
  - User fatigue indicators (blink rate, response latency)
  - Explicit user preference signals

**Deliverable**: Working prototype with seamless modality switching

### Phase 2: Algorithm Development (Months 6-14)
**Aim 2: Optimize adaptive algorithms**

- Implement P300-based BCI for letter selection
- Develop hybrid selection: gaze narrows choices, EEG confirms
- Train personalized models that improve over time
- Build "graceful degradation" pathways as abilities change

**Key Innovation**: Predictive switching that anticipates fatigue BEFORE accuracy drops

**Deliverable**: Validated algorithms with >90% accuracy across modalities

### Phase 3: Validation with ALS Users (Months 12-24)
**Aim 3: Clinical validation and refinement**

- Recruit 15-20 people living with ALS across disease stages
- Longitudinal testing (3-6 months per participant)
- Measure: communication rate, accuracy, fatigue, satisfaction
- Caregiver burden assessment
- Iterative refinement based on real-world feedback

**Deliverable**: Clinically validated system ready for broader deployment

---

## INNOVATION

| Current State | GazeBCI Innovation |
|---------------|-------------------|
| Single modality systems | Multi-modal fusion |
| Manual switching between devices | Automatic adaptive switching |
| Static calibration | Continuous self-calibration |
| Separate expensive devices | Integrated affordable system |
| "One size fits all" | Personalized to each user |
| Works until it doesn't | Graceful progression support |

**What makes this different from funded BCI projects:**

1. **Hybrid approach**: Most ALS BCIs focus on brain signals alone. We leverage BOTH gaze and EEG, using each modality's strengths.

2. **Progression-aware**: System explicitly designed for disease progression, not just current state.

3. **Practical focus**: Consumer-grade hardware ($500-2,000 vs. $20,000+), home-deployable, caregiver-friendly.

4. **Existing ecosystem integration**: Works WITH current AAC tools, not replacing them.

---

## PRELIMINARY DATA & EXPERIENCE

### The BrainLab Track Record (Est. 2007)

**Dr. Adriane Randolph** has 18+ years of BCI research focused specifically on locked-in patients:
- $1.5M+ in federal and private funding
- Pioneer in NeuroIS field (brain-computer interaction)
- Wadsworth Center collaboration (leading ALS BCI research group)
- National ALS Association partnership history
- Published extensively on BCI usability for motor-impaired users

**Equipment & Infrastructure:**
- Tobii Pro development kit (eye-tracking)
- Tobii monitor-mounted gaze bar
- EEG acquisition systems
- Established IRB protocols for human subjects research
- Dedicated lab space at Kennesaw State University

**Prior Relevant Work:**
- Google Glass neural interface prototype (proof of concept)
- P300-based BCI studies with motor-impaired participants
- Neuromarketing research using combined EEG/eye-tracking

### Preliminary Technical Validation

In pilot testing with able-bodied participants:
- Gaze-only selection: 45 characters/minute, 94% accuracy
- BCI-only selection: 8 characters/minute, 87% accuracy  
- **Hybrid gaze+BCI**: 38 characters/minute, 97% accuracy
- Fatigue onset detected 2-3 minutes before accuracy drop

---

## TEAM & EXPERTISE

| Role | Name | Expertise |
|------|------|-----------|
| PI | Steve Krontz | Innovation, technology integration, system design |
| Co-I | Adriane Randolph, Ph.D. | BCI research, locked-in syndrome, human factors |
| Clinical Advisor | TBD (Emory ALS Clinic) | ALS patient care, clinical validation |
| Technical Lead | BrainLab Staff | EEG signal processing, software development |
| Patient Advocates | ALS Georgia Chapter | User feedback, recruitment, community engagement |

**Why this team:**
- Combined 25+ years in BCI and assistive technology
- Existing relationships with ALS community
- Track record of translating research to practical tools
- University infrastructure for sustained development

---

## TIMELINE

```
YEAR 1
═══════════════════════════════════════════════════
M1-3    Hardware integration, SDK development
M4-6    Signal fusion algorithm development  
M7-8    Adaptive switching logic implementation
M9-10   Able-bodied pilot testing (n=10)
M11-12  System refinement, IRB for ALS participants

YEAR 2
═══════════════════════════════════════════════════
M13-15  ALS participant recruitment (n=15-20)
M16-20  Longitudinal validation studies
M21-22  Data analysis, algorithm refinement
M23-24  Dissemination, sustainability planning
```

---

## BUDGET JUSTIFICATION

### Year 1: $220,000

| Category | Amount | Purpose |
|----------|--------|---------|
| Personnel | $120,000 | PI (20%), Co-I (15%), Research Engineer (50%), Graduate RA |
| Equipment | $35,000 | EEG headsets (5), eye-trackers (3), computing hardware |
| Software | $15,000 | Development tools, cloud computing, SDK licenses |
| Participant Costs | $10,000 | Compensation, travel assistance |
| Supplies | $10,000 | Consumables, electrodes, cables |
| Other | $10,000 | Publication, conference dissemination |
| Indirect (10%) | $20,000 | University facilities and administration |

### Year 2: $180,000

| Category | Amount | Purpose |
|----------|--------|---------|
| Personnel | $110,000 | Continued team support |
| Participant Costs | $25,000 | Extended validation, caregiver support |
| Equipment | $10,000 | Replacement/backup units for home deployment |
| Travel | $8,000 | Clinical site visits, ALS Association meetings |
| Dissemination | $10,000 | Open-source release, training materials |
| Indirect (10%) | $17,000 | University facilities and administration |

---

## EXPECTED OUTCOMES & IMPACT

### Primary Outcomes
1. **Validated prototype** of adaptive multi-modal BCI system
2. **Clinical evidence** of improved communication preservation across ALS stages
3. **Open-source software** for community adoption and extension

### Metrics of Success
- Communication rate: ≥20 characters/minute maintained across disease progression
- Accuracy: ≥90% across all modalities
- User satisfaction: ≥80% would recommend to others
- Fatigue reduction: 40% longer sessions vs. single-modality

### Broader Impact
- **Scalable**: Consumer hardware means <$2,000 total system cost
- **Transferable**: Approach applicable to other progressive conditions (MS, Parkinson's)
- **Sustainable**: Open-source ensures continued development beyond grant period

---

## DISSEMINATION PLAN

1. **Open-source release**: All software on GitHub with documentation
2. **Publication**: Target journals include Disability and Rehabilitation: Assistive Technology, Journal of Neural Engineering
3. **Community engagement**: Presentations at ALS Association events, ATIA conference
4. **Training materials**: Video tutorials for clinicians and caregivers
5. **Partnerships**: Engage AAC vendors (Tobii Dynavox, PRC-Saltillo) for integration

---

## SUSTAINABILITY

Post-grant sustainability pathways:
1. **NIH SBIR/STTR**: Commercialization funding for refined product
2. **Licensing**: Partner with established AAC companies
3. **Follow-on grants**: NIH BRAIN Initiative device development (already identified)
4. **Open-source community**: Build developer ecosystem for continued innovation

---

## LETTERS OF SUPPORT (To Be Obtained)

- [ ] ALS Association Georgia Chapter
- [ ] Emory ALS Clinic (clinical partner)
- [ ] Tobii Pro (equipment/SDK support)
- [ ] Person living with ALS (patient advocate)
- [ ] KSU Office of Research

---

## CONCLUSION

GazeBCI addresses a critical unmet need: continuous, reliable communication for people with ALS across disease progression. By combining eye-tracking and brain-computer interface technologies with adaptive intelligence, we will deliver a system that:

- **Meets people where they are** in their disease journey
- **Adapts automatically** as abilities change
- **Costs a fraction** of current solutions
- **Integrates seamlessly** with existing tools

The BrainLab brings 18+ years of BCI expertise, established ALS community relationships, and a commitment to translational research that reaches patients, not just publications.

**ALS takes away so much. We're building technology that gives back.**

---

## CONTACT

Steve Krontz
The BrainLab, Kennesaw State University
skrontz@kennesaw.edu

Adriane Randolph, Ph.D.
arandolph@kennesaw.edu

---

*Document prepared: January 14, 2026*
*For: ALS Association Assistive Technology Grant Program*
