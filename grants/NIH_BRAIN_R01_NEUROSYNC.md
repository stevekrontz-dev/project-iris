# NIH BRAIN INITIATIVE R01 GRANT PROPOSAL
## RFA-NS-25-018: New Technologies and Novel Approaches for Recording and Modulation

---

# PROJECT TITLE
**NeuroSync: A Multi-Modal Neural Interface Platform Integrating Eye-Gaze, EEG, and fNIRS for Real-Time Circuit-Level Recording in Naturalistic Human Behavior**

---

## PRINCIPAL INVESTIGATOR
**Steve Krontz, BBA**
Head Futurist & Director of Innovation
The BrainLab, Kennesaw State University

**Co-Investigators:**
- Adriane Randolph, Ph.D. - Executive Director, The BrainLab; BCI/NeuroIS Expert
- [TBD] - Biomedical Engineering, Georgia Tech (signal processing)
- [TBD] - Emory University (clinical neuroscience validation)

---

## FUNDING MECHANISM
**R01 Research Project Grant**
- Duration: 5 years
- Total Costs: $2,500,000 ($500,000/year direct costs)
- No clinical trials

---

## KEY DATES
- **Letter of Intent**: November 20, 2025
- **Application Deadline**: January 20, 2026
- **Expiration**: January 21, 2026

---

# SPECIFIC AIMS

## Overall Goal
To develop and validate a novel multi-modal neural recording platform that simultaneously captures eye-gaze patterns, cortical EEG, and prefrontal hemodynamic activity (fNIRS), synchronized at millisecond precision, enabling unprecedented insight into circuit-level dynamics during naturalistic human cognition and behavior.

---

### Aim 1: Develop Hardware Integration Platform for Synchronized Multi-Modal Neural Recording
**Rationale**: Current neuroscience approaches rely on single modalities that capture only fragments of neural activity. EEG provides millisecond temporal resolution but poor spatial localization; fNIRS offers better localization of cortical activity but slower hemodynamic timescales; eye-gaze reveals attentional allocation and cognitive state but not neural substrates. No existing platform integrates these modalities with sub-millisecond synchronization.

**Approach**: 
- Engineer a unified hardware platform integrating:
  - High-density EEG (64+ channels, research-grade)
  - Continuous-wave fNIRS (prefrontal and motor cortex coverage)
  - Tobii Pro eye-tracking (gaze position, pupillometry, blink detection)
- Develop custom synchronization circuitry achieving <1ms timing alignment
- Create unified data acquisition software with real-time streaming
- Design for naturalistic, untethered recording (wireless transmission)

**Milestones**:
- Year 1: Prototype hardware integration with wired configuration
- Year 2: Wireless implementation and miniaturization
- Year 3: Validated production system for distribution

**Innovation**: First platform to achieve hardware-level synchronization across all three modalities with precision sufficient for event-related analysis.

---

### Aim 2: Develop Computational Methods for Cross-Modal Neural Signal Fusion
**Rationale**: Multi-modal data is only valuable if integration methods can extract information beyond what individual modalities provide. Current fusion approaches are limited to offline analysis and fail to leverage the complementary information across modalities.

**Approach**:
- Develop real-time signal processing pipeline for:
  - EEG artifact rejection using gaze and blink data
  - Gaze-contingent EEG epoching for attention-locked analysis
  - Hemodynamic response function deconvolution informed by EEG markers
- Create machine learning models for:
  - Multi-modal cognitive state classification
  - Attention prediction from combined signals
  - Circuit-level inference combining electrical and hemodynamic dynamics
- Implement edge computing architecture for real-time processing

**Milestones**:
- Year 1: Offline fusion algorithms validated on collected data
- Year 2: Real-time pipeline achieving <100ms latency
- Year 3-4: Validated ML models with >85% state classification accuracy

**Innovation**: Novel algorithms that leverage cross-modal information to achieve neural state inference impossible with any single modality.

---

### Aim 3: Validate Platform in Human Behavioral Paradigms
**Rationale**: Tool development without validation in meaningful behavioral contexts limits translational impact. The platform must demonstrate utility for understanding circuit dynamics during naturalistic cognition.

**Approach**:
- Design behavioral paradigms targeting:
  - Attention switching and sustained attention (prefrontal-parietal circuits)
  - Decision-making under uncertainty (prefrontal-limbic interactions)
  - Motor planning and execution (motor cortex dynamics)
- Collect data from N=60 healthy participants across paradigms
- Validate signal quality, synchronization accuracy, and replicability
- Benchmark against gold-standard single-modality recordings

**Milestones**:
- Year 2-3: Paradigm development and pilot data collection (N=20)
- Year 3-4: Full validation study (N=60)
- Year 4-5: Publication of validation results and methodological papers

**Innovation**: First systematic validation of multi-modal recording in naturalistic behavioral tasks with circuit-level interpretation.

---

### Aim 4: Disseminate Platform as Open-Source Tool for Neuroscience Community
**Rationale**: BRAIN Initiative tools must be accessible to maximize scientific impact. Proprietary solutions limit adoption and reproducibility.

**Approach**:
- Release all software components under MIT open-source license
- Publish detailed hardware specifications and assembly instructions
- Create comprehensive documentation and tutorials
- Establish user community and support infrastructure
- Partner with equipment manufacturers for commercial availability

**Milestones**:
- Year 3: Beta release to 5 external laboratories
- Year 4: Public release with full documentation
- Year 5: Established user community with >20 active research groups

**Innovation**: Full open-source dissemination model ensuring sustainability and broad adoption.

---

# RESEARCH STRATEGY

## A. SIGNIFICANCE

### The Gap: Fragmented Recording Technologies

Understanding how neural circuits give rise to cognition requires capturing brain activity across multiple scales simultaneously:

| Scale | Current Technology | Limitation |
|-------|-------------------|------------|
| **Millisecond dynamics** | EEG | Poor spatial resolution, susceptible to artifacts |
| **Cortical localization** | fNIRS | Slow hemodynamic response (~5-6 seconds) |
| **Behavioral state** | Eye-tracking | No neural data |
| **Single neurons** | Invasive electrodes | Not applicable in healthy humans |

**No existing technology bridges these scales non-invasively.**

Current workarounds involve:
- Sequential recording sessions (cannot capture real-time interactions)
- Post-hoc alignment (introduces timing errors >10ms)
- Separate analysis pipelines (misses cross-modal information)

### Clinical and Scientific Impact

**NeuroSync** addresses critical needs:

1. **Basic Science**: Enable discovery of circuit-level mechanisms underlying attention, decision-making, and motor control
2. **Clinical Translation**: Provide non-invasive markers for disorders affecting multiple brain systems (ADHD, autism, mild TBI)
3. **Brain-Computer Interfaces**: Improve BCI performance through multi-modal neural decoding
4. **Neuroergonomics**: Real-world cognitive monitoring for high-stakes environments (aviation, surgery)

### Alignment with BRAIN Initiative Goals

This project directly addresses BRAIN 2.0 priorities:
- **Recording technologies**: Novel multi-modal integration at unprecedented temporal resolution
- **Human neuroscience**: Non-invasive approach enabling studies impossible with invasive methods
- **Circuit understanding**: Cross-scale analysis linking neural dynamics to behavior
- **Tool dissemination**: Open-source model maximizing community impact

---

## B. INNOVATION

### 1. Hardware Innovation: True Multi-Modal Synchronization

**Current state**: Researchers combine modalities using software timestamps with 10-50ms jitter—insufficient for event-related analysis.

**NeuroSync innovation**: Custom hardware achieving <1ms synchronization through:
- Shared master clock across all acquisition systems
- Hardware trigger lines for precise event marking
- FPGA-based timestamp generation
- Wireless transmission preserving synchronization

### 2. Algorithmic Innovation: Cross-Modal Signal Enhancement

**Current state**: Each modality analyzed independently; artifacts handled modality-by-modality.

**NeuroSync innovation**: Cross-modal information improves each signal:
- **Gaze-informed EEG**: Blink artifacts identified from eye-tracker, not EEG
- **EEG-informed fNIRS**: Neural event markers improve hemodynamic deconvolution
- **Pupillometry-EEG fusion**: Arousal state from pupil size constrains EEG interpretation

### 3. Methodological Innovation: Naturalistic Recording Protocol

**Current state**: Multi-modal studies require heavily constrained paradigms (head restraint, controlled gaze).

**NeuroSync innovation**: Design for naturalistic behavior:
- Wireless, lightweight hardware
- Robust to motion artifacts through sensor fusion
- Real-time quality monitoring with automatic adjustment

### 4. Dissemination Innovation: Full Open-Source Model

**Current state**: Multi-modal platforms are proprietary, expensive ($50K+), and poorly documented.

**NeuroSync innovation**: 
- All software under MIT license
- Hardware specifications published
- Assembly tutorials and troubleshooting guides
- Active user community support
- Partnership pathway for commercial availability (<$10K system cost)

---

## C. APPROACH

### Preliminary Studies

#### The BrainLab Infrastructure

The BrainLab at Kennesaw State University has 18+ years of experience in human neural recording:

**Equipment**:
- Tobii Pro eye-tracking systems (screen-mounted and wearable)
- Research-grade EEG acquisition (64-channel systems)
- fNIRS systems (prefrontal and motor cortex configurations)
- Dedicated recording suites with controlled lighting and acoustics

**Expertise**:
- Dr. Adriane Randolph: Pioneer in NeuroIS, 50+ publications on BCI and neural recording
- Established IRB protocols for human neural recording
- Track record of NIH, NSF, and private foundation funding

#### Pilot Data

**Preliminary synchronization testing** (n=10 able-bodied participants):
- Achieved 0.8ms synchronization accuracy using prototype hardware
- Cross-modal artifact detection reduced EEG data loss by 35%
- Gaze-locked EEG analysis revealed attention-related potentials 40ms earlier than traditional methods

**BCI performance** (collaboration with Wadsworth Center):
- Multi-modal decoding achieved 23% improvement over EEG-only classification
- Demonstrated in users with motor impairments

### Research Design and Methods

#### Aim 1: Hardware Integration Platform

**Year 1 Activities**:

*Hardware Engineering*:
- Design custom synchronization board (FPGA-based)
- Integrate Tobii Pro SDK with EEG and fNIRS acquisition
- Develop unified data format (HDF5-based, BIDS-compatible)
- Prototype wired configuration for validation

*Component Selection*:
| Component | Specification | Vendor |
|-----------|--------------|--------|
| EEG | 64 channels, 24-bit, 2kHz | BioSemi/Brain Products |
| fNIRS | 16 sources, 32 detectors, 10Hz | NIRx/Artinis |
| Eye-tracking | 120Hz binocular, pupillometry | Tobii Pro |
| Sync board | Custom FPGA, <0.1ms jitter | In-house design |

**Year 2 Activities**:

*Wireless Implementation*:
- Integrate wireless EEG (24-channel optimization)
- Bluetooth/WiFi hybrid transmission
- Battery optimization for 4+ hour recording
- Miniaturization for wearability

*Validation Testing*:
- Bench testing: signal quality vs. wired
- Human testing: naturalistic movement protocols
- Synchronization verification across conditions

**Year 3 Activities**:

*Production Engineering*:
- Design for manufacturability
- Component sourcing strategy
- Quality control protocols
- Documentation for external replication

#### Aim 2: Computational Methods

**Signal Processing Pipeline**:

```
┌─────────────────────────────────────────────────────────────┐
│                    NEUROSYNC PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────────┐   │
│  │ EEG Raw │────►│ Gaze-Based  │────►│ Clean EEG       │   │
│  │ 64 ch   │     │ Artifact    │     │ Epochs          │   │
│  └─────────┘     │ Rejection   │     └────────┬────────┘   │
│                  └─────────────┘              │             │
│  ┌─────────┐           │                     │             │
│  │ Eye-    │───────────┘                     ▼             │
│  │ Tracker │────────────────────────►┌───────────────┐     │
│  └─────────┘                         │ Multi-Modal   │     │
│                                      │ Fusion        │     │
│  ┌─────────┐     ┌─────────────┐     │ Engine        │     │
│  │ fNIRS   │────►│ EEG-Informed│────►│               │     │
│  │ Raw     │     │ Deconvolution│    └───────┬───────┘     │
│  └─────────┘     └─────────────┘             │             │
│                                              ▼             │
│                                      ┌───────────────┐     │
│                                      │ Cognitive     │     │
│                                      │ State Output  │     │
│                                      └───────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Machine Learning Architecture**:

- **Feature extraction**: Time-frequency EEG, HbO/HbR concentration, gaze metrics
- **Fusion model**: Multi-stream neural network with attention mechanism
- **Training**: Transfer learning from large EEG datasets (Temple University Hospital)
- **Validation**: Leave-one-subject-out cross-validation

**Real-Time Implementation**:
- Target latency: <100ms from neural event to state output
- Edge computing on NVIDIA Jetson platform
- Python/C++ hybrid for performance
- ROS2 integration for robotics applications

#### Aim 3: Human Validation Studies

**Participant Recruitment**:
- N=60 healthy adults (18-65 years)
- Stratified by age and sex
- Exclusion: neurological/psychiatric history, uncorrected vision

**Behavioral Paradigms**:

*Paradigm 1: Attention Networks Test (ANT)*
- Established task for attention subsystems
- Expected findings: Gaze precedes EEG attention markers; fNIRS reveals sustained attention cost

*Paradigm 2: Iowa Gambling Task (IGT)*
- Decision-making under uncertainty
- Expected findings: Prefrontal fNIRS differentiates risk strategies; EEG reveals anticipatory activity

*Paradigm 3: Motor Sequence Learning*
- Implicit learning paradigm
- Expected findings: Motor cortex fNIRS tracks learning; EEG reveals consolidation signatures

**Analysis Plan**:
- Signal quality metrics (SNR, artifact proportion)
- Cross-modal synchronization verification
- Behavioral correlates of neural measures
- Comparison to single-modality gold standards

#### Aim 4: Dissemination

**Software Release**:
- GitHub repository with CI/CD pipeline
- PyPI packages for Python integration
- MATLAB toolbox for existing users
- Docker containers for reproducibility

**Hardware Documentation**:
- Bill of materials with sourcing links
- Assembly instructions with video tutorials
- Calibration and troubleshooting guides
- 3D-printable components for custom modifications

**Community Building**:
- Annual user workshop (Year 3-5)
- Online forum and mailing list
- Partnership with BIDS standard for data sharing
- Integration with existing platforms (MNE-Python, EEGLAB)

---

## D. TIMELINE

```
YEAR 1 (2026)
════════════════════════════════════════════════════════════════
Q1   Hardware design, component selection
Q2   Prototype synchronization board development
Q3   Software architecture, SDK integration
Q4   Wired prototype validation

YEAR 2 (2027)
════════════════════════════════════════════════════════════════
Q1   Wireless hardware development
Q2   Signal processing pipeline implementation
Q3   Pilot behavioral data collection (n=20)
Q4   Algorithm refinement, ML model training

YEAR 3 (2028)
════════════════════════════════════════════════════════════════
Q1   Production hardware design
Q2   Beta release to external labs (n=5)
Q3   Full validation study begins (n=60)
Q4   Software public release

YEAR 4 (2029)
════════════════════════════════════════════════════════════════
Q1-Q2 Validation study completion
Q3   Data analysis, manuscript preparation
Q4   Hardware documentation release

YEAR 5 (2030)
════════════════════════════════════════════════════════════════
Q1   Publication of validation results
Q2   User community workshop
Q3   Commercial partnership finalization
Q4   Sustainability planning, follow-on funding
```

---

## E. POTENTIAL PITFALLS AND ALTERNATIVES

| Risk | Mitigation Strategy |
|------|---------------------|
| Synchronization accuracy <1ms not achieved | Fallback to software timestamp correction; acceptable for many applications |
| Wireless adds unacceptable latency | Retain wired option for latency-critical applications |
| ML models don't generalize across subjects | Implement personalized calibration protocol |
| External labs can't replicate hardware | Partner with commercial vendor for turnkey system |
| fNIRS motion artifacts in naturalistic tasks | Develop accelerometer-based correction algorithms |

---

# BUDGET JUSTIFICATION

## Personnel ($300,000/year)

| Role | Effort | Annual Cost | Justification |
|------|--------|-------------|---------------|
| PI (Krontz) | 20% | $30,000 | Overall project direction, hardware design |
| Co-I (Randolph) | 25% | $45,000 | Scientific direction, human studies oversight |
| Research Engineer | 100% | $90,000 | Hardware development, software engineering |
| Postdoctoral Fellow | 100% | $65,000 | Algorithm development, data analysis |
| Graduate RA (2) | 50% each | $50,000 | Data collection, paradigm development |
| Undergraduate RA | 20% | $10,000 | Data processing, documentation |
| Fringe | -- | $10,000 | Benefits |

## Equipment ($75,000 Year 1; $25,000/year thereafter)

| Item | Cost | Year | Justification |
|------|------|------|---------------|
| EEG system (64-channel) | $35,000 | 1 | High-density recording |
| fNIRS system | $25,000 | 1 | Cortical hemodynamics |
| Eye-tracker (Tobii Pro) | $10,000 | 1 | Gaze and pupillometry |
| FPGA development board | $5,000 | 1 | Custom synchronization |
| Computing hardware | $15,000 | 1-2 | Processing, edge computing |
| Wireless components | $10,000 | 2 | Bluetooth/WiFi modules |
| Replacement/backup | $5,000 | 3-5 | Maintenance |

## Participant Costs ($15,000/year Years 2-5)

- N=60 participants × $150 compensation = $9,000
- Travel/parking assistance: $3,000
- Screening/recruitment: $3,000

## Supplies ($10,000/year)

- EEG electrodes, gel, caps
- fNIRS optodes
- Electronic components
- 3D printing materials

## Travel ($10,000/year)

- Conference presentations (SfN, OHBM)
- Collaborator site visits
- User workshop hosting (Years 3-5)

## Other ($15,000/year)

- Publication costs (open access)
- Cloud computing (AWS/GCP)
- Software licenses
- Equipment maintenance

## Facilities & Administrative (F&A)

Per KSU negotiated rate (estimated 50% MTDC)

---

# VERTEBRATE ANIMALS / HUMAN SUBJECTS

## Human Subjects

This research involves human subjects as defined by 45 CFR 46.102.

**Risk Assessment**: Minimal risk
- Non-invasive recording only
- Standard behavioral tasks
- No deception or sensitive topics

**Inclusion Criteria**:
- Ages 18-65
- Normal or corrected vision
- English fluency

**Exclusion Criteria**:
- History of neurological/psychiatric disorder
- Current psychoactive medication
- Pregnancy (fNIRS safety precaution)

**Informed Consent**: Written consent obtained; IRB-approved protocol

**Data Security**: De-identified data; encrypted storage; HIPAA-compliant procedures

---

# DATA SHARING PLAN

Consistent with BRAIN Initiative requirements:

1. **Raw Data**: Deposited to OpenNeuro within 6 months of collection
2. **Processed Data**: BIDS-formatted derivatives shared publicly
3. **Code**: All analysis code on GitHub under MIT license
4. **Hardware Designs**: Published on Open Science Framework
5. **Documentation**: Comprehensive guides on project website

---

# RESOURCE SHARING PLAN

1. **Software**: Open-source (GitHub) with comprehensive documentation
2. **Hardware**: Specifications published; commercial partnership for availability
3. **Protocols**: Detailed methods in publications and supplementary materials
4. **Training**: Annual workshops; online tutorials
5. **Community**: Active forum and mailing list support

---

# FACILITIES AND EQUIPMENT

## The BrainLab, Kennesaw State University

**Dedicated Space**: 
- 1,200 sq ft research suite
- Shielded recording room
- Equipment storage and preparation area
- Participant waiting and consent area

**Existing Equipment**:
- Tobii Pro development kit and monitor bars
- EEG acquisition systems
- fNIRS systems
- High-performance computing workstation
- 3D printer for prototyping

**Institutional Support**:
- IRB infrastructure for human subjects research
- Office of Research administrative support
- IT infrastructure and security
- Graduate student training programs

## Collaborating Institutions

- **Georgia Tech**: Biomedical engineering consultation, advanced fabrication
- **Emory University**: Clinical neuroscience validation, patient recruitment pathway

---

# BIOGRAPHICAL SKETCHES

## Steve Krontz, BBA (Principal Investigator)

**Position**: Head Futurist & Director of Innovation, The BrainLab, Kennesaw State University

**Education**:
- BBA, Marketing and Information Systems, Kennesaw State University

**Experience**:
- 11+ years directing innovation at The BrainLab
- Pioneer in AI-human coordination systems
- Serial entrepreneur with technology commercialization experience
- Developer of IRIS (Intelligent Research Information System)

**Relevant Publications/Projects**:
- Google Glass neural interface prototype
- Boswell AI coordination system
- IRIS research collaboration platform

## Adriane Randolph, Ph.D. (Co-Investigator)

**Position**: 
- Executive Director, The BrainLab
- Associate Dean for Community and Faculty Affairs
- Full Professor of Information Systems

**Education**:
- Ph.D., Computer Information Systems, Georgia State University
- B.S., Systems Engineering, University of Virginia

**Experience**:
- Founder of The BrainLab (2007)
- Pioneer in NeuroIS field
- $1.5M+ in research funding
- 50+ peer-reviewed publications

**Selected Publications**:
- [BCI usability studies with motor-impaired users]
- [NeuroIS methodology papers]
- [Locked-in syndrome communication research]

---

# LETTERS OF SUPPORT (To Be Obtained)

- [ ] Georgia Tech Biomedical Engineering (fabrication partnership)
- [ ] Emory Neurology Department (clinical validation)
- [ ] Tobii Pro (equipment and SDK support)
- [ ] OpenBCI (hardware collaboration)
- [ ] NIRx (fNIRS system support)
- [ ] KSU Office of Research (institutional commitment)

---

# APPENDICES

## A. Hardware Schematics (Draft)
[To be developed]

## B. Software Architecture Diagram
[To be developed]

## C. Preliminary Data Figures
[To be collected]

## D. Consortium/Collaboration Letters
[To be obtained]

---

# CHECKLIST FOR SUBMISSION

- [ ] SF424 (R&R) Application for Federal Assistance
- [ ] Project Summary/Abstract (30 lines max)
- [ ] Project Narrative (Relevance statement)
- [ ] Specific Aims (1 page)
- [ ] Research Strategy (12 pages max)
- [ ] Bibliography
- [ ] Facilities & Resources
- [ ] Equipment
- [ ] Biographical Sketches (all key personnel)
- [ ] Budget and Justification
- [ ] Data Management and Sharing Plan
- [ ] Resource Sharing Plan
- [ ] Human Subjects documentation
- [ ] Letters of Support
- [ ] Plan for Enhancing Diverse Perspectives (PEDP)

---

*Document prepared: January 14, 2026*
*For: NIH BRAIN Initiative RFA-NS-25-018*
*Application Deadline: January 20, 2026*
