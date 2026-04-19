"""Expanded code catalog for CHC Pro AI.

Provides ~550 entries across ICD-10-CM, ICD-10-PCS, CPT, HCPCS, Revenue,
Condition, Occurrence, Value codes and an MS-DRG/APR-DRG mapping table.
Each entry ships with a guideline citation so downstream output can be
audited.
"""
from __future__ import annotations
from typing import List

# --------------------------------------------------------------------------
# ICD-10-CM (diagnoses) — ~320 entries across major chapters
# --------------------------------------------------------------------------
ICD10_CM: List[dict] = [
    # Ch. 1 — Infectious diseases
    {"keywords": ["sepsis"], "code": "A41.9", "description": "Sepsis, unspecified organism", "ref": "ICD-10-CM Ch. 1 I.C.1.d"},
    {"keywords": ["severe sepsis"], "code": "R65.20", "description": "Severe sepsis without septic shock", "ref": "ICD-10-CM Ch. 1 I.C.1.d.2"},
    {"keywords": ["septic shock"], "code": "R65.21", "description": "Severe sepsis with septic shock", "ref": "ICD-10-CM Ch. 1 I.C.1.d.2"},
    {"keywords": ["bacteremia"], "code": "R78.81", "description": "Bacteremia", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["mrsa"], "code": "A49.02", "description": "MRSA infection, unspecified site", "ref": "ICD-10-CM Ch. 1"},
    {"keywords": ["clostridium difficile", "c. diff", "c diff"], "code": "A04.7", "description": "Enterocolitis due to Clostridium difficile", "ref": "ICD-10-CM Ch. 1"},
    {"keywords": ["tuberculosis", "tb"], "code": "A15.9", "description": "Respiratory tuberculosis, unspecified", "ref": "CMS LCD L34091"},
    {"keywords": ["influenza", "flu"], "code": "J11.1", "description": "Influenza with other respiratory manifestations", "ref": "CDC/CMS Flu Coding"},
    {"keywords": ["covid", "coronavirus", "sars-cov-2", "covid-19"], "code": "U07.1", "description": "COVID-19", "ref": "CDC/CMS COVID-19 Coding Guidelines"},
    {"keywords": ["post covid", "long covid"], "code": "U09.9", "description": "Post COVID-19 condition, unspecified", "ref": "CDC ICD-10-CM Guidance"},
    {"keywords": ["hepatitis a"], "code": "B15.9", "description": "Hepatitis A without hepatic coma", "ref": "ICD-10-CM Ch. 1"},
    {"keywords": ["hepatitis b"], "code": "B16.9", "description": "Acute hepatitis B without delta-agent and without hepatic coma", "ref": "ICD-10-CM Ch. 1"},
    {"keywords": ["hepatitis c"], "code": "B19.20", "description": "Unspecified viral hepatitis C without hepatic coma", "ref": "ICD-10-CM Ch. 1"},
    {"keywords": ["hiv", "human immunodeficiency virus"], "code": "B20", "description": "Human immunodeficiency virus [HIV] disease", "ref": "ICD-10-CM Ch. 1 I.C.1.a"},
    {"keywords": ["cellulitis"], "code": "L03.90", "description": "Cellulitis, unspecified", "ref": "ICD-10-CM Ch. 12"},
    {"keywords": ["herpes zoster", "shingles"], "code": "B02.9", "description": "Zoster without complications", "ref": "ICD-10-CM Ch. 1"},
    {"keywords": ["meningitis"], "code": "G03.9", "description": "Meningitis, unspecified", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["pneumonia", "pneumonitis"], "code": "J18.9", "description": "Pneumonia, unspecified organism", "ref": "CMS LCD L35023 — Pneumonia coverage policy"},
    {"keywords": ["community acquired pneumonia", "cap"], "code": "J15.9", "description": "Unspecified bacterial pneumonia", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["aspiration pneumonia"], "code": "J69.0", "description": "Pneumonitis due to inhalation of food and vomit", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["viral pneumonia"], "code": "J12.9", "description": "Viral pneumonia, unspecified", "ref": "ICD-10-CM Ch. 10"},

    # Ch. 2 — Neoplasms
    {"keywords": ["breast cancer", "malignant neoplasm of breast"], "code": "C50.919", "description": "Malignant neoplasm of unspecified site of unspecified female breast", "ref": "ICD-10-CM Ch. 2 I.C.2"},
    {"keywords": ["lung cancer", "malignant neoplasm of lung"], "code": "C34.90", "description": "Malignant neoplasm of unspecified part of unspecified bronchus or lung", "ref": "CMS LCD L34389"},
    {"keywords": ["prostate cancer"], "code": "C61", "description": "Malignant neoplasm of prostate", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["colon cancer", "colorectal cancer"], "code": "C18.9", "description": "Malignant neoplasm of colon, unspecified", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["pancreatic cancer"], "code": "C25.9", "description": "Malignant neoplasm of pancreas, unspecified", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["leukemia"], "code": "C95.90", "description": "Leukemia, unspecified of unspecified cell type", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["lymphoma"], "code": "C85.90", "description": "Non-Hodgkin lymphoma, unspecified, unspecified site", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["melanoma"], "code": "C43.9", "description": "Malignant melanoma of skin, unspecified", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["brain tumor", "glioma"], "code": "C71.9", "description": "Malignant neoplasm of brain, unspecified", "ref": "ICD-10-CM Ch. 2"},
    {"keywords": ["benign neoplasm"], "code": "D36.9", "description": "Benign neoplasm, unspecified site", "ref": "ICD-10-CM Ch. 2"},

    # Ch. 3 — Blood / immune
    {"keywords": ["anemia"], "code": "D64.9", "description": "Anemia, unspecified", "ref": "ICD-10-CM Ch. 3"},
    {"keywords": ["iron deficiency anemia"], "code": "D50.9", "description": "Iron deficiency anemia, unspecified", "ref": "ICD-10-CM Ch. 3"},
    {"keywords": ["thrombocytopenia"], "code": "D69.6", "description": "Thrombocytopenia, unspecified", "ref": "ICD-10-CM Ch. 3"},
    {"keywords": ["coagulopathy"], "code": "D68.9", "description": "Coagulation defect, unspecified", "ref": "ICD-10-CM Ch. 3"},
    {"keywords": ["sickle cell"], "code": "D57.1", "description": "Sickle-cell disease without crisis", "ref": "ICD-10-CM Ch. 3"},

    # Ch. 4 — Endocrine, nutritional, metabolic
    {"keywords": ["type 2 diabetes", "t2dm", "diabetes mellitus type 2", "dm type 2"], "code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "ref": "ICD-10-CM Ch. 4 I.C.4.a"},
    {"keywords": ["type 1 diabetes", "t1dm"], "code": "E10.9", "description": "Type 1 diabetes mellitus without complications", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["diabetic ketoacidosis", "dka"], "code": "E11.10", "description": "Type 2 diabetes with ketoacidosis without coma", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["diabetic nephropathy", "diabetes with kidney"], "code": "E11.21", "description": "Type 2 diabetes with diabetic nephropathy", "ref": "ICD-10-CM Ch. 4 I.C.4.a.2"},
    {"keywords": ["diabetic retinopathy"], "code": "E11.319", "description": "Type 2 diabetes with unspecified diabetic retinopathy without macular edema", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["hyperglycemia"], "code": "R73.9", "description": "Hyperglycemia, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["hypoglycemia"], "code": "E16.2", "description": "Hypoglycemia, unspecified", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["hyperthyroidism", "thyrotoxicosis"], "code": "E05.90", "description": "Thyrotoxicosis, unspecified without thyrotoxic crisis or storm", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["hypothyroidism"], "code": "E03.9", "description": "Hypothyroidism, unspecified", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["obesity"], "code": "E66.9", "description": "Obesity, unspecified", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["morbid obesity"], "code": "E66.01", "description": "Morbid (severe) obesity due to excess calories", "ref": "CMS LCD L35022"},
    {"keywords": ["hyperlipidemia", "dyslipidemia", "high cholesterol"], "code": "E78.5", "description": "Hyperlipidemia, unspecified", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["hypokalemia"], "code": "E87.6", "description": "Hypokalemia", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["hyperkalemia"], "code": "E87.5", "description": "Hyperkalemia", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["hyponatremia"], "code": "E87.1", "description": "Hypo-osmolality and hyponatremia", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["dehydration", "volume depletion"], "code": "E86.0", "description": "Dehydration", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["malnutrition"], "code": "E46", "description": "Unspecified protein-calorie malnutrition", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["vitamin d deficiency"], "code": "E55.9", "description": "Vitamin D deficiency, unspecified", "ref": "ICD-10-CM Ch. 4"},

    # Ch. 5 — Mental / behavioral
    {"keywords": ["depression", "major depressive"], "code": "F32.9", "description": "Major depressive disorder, single episode, unspecified", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["recurrent depression"], "code": "F33.9", "description": "Major depressive disorder, recurrent, unspecified", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["anxiety"], "code": "F41.9", "description": "Anxiety disorder, unspecified", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["generalized anxiety", "gad"], "code": "F41.1", "description": "Generalized anxiety disorder", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["bipolar"], "code": "F31.9", "description": "Bipolar disorder, unspecified", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["schizophrenia"], "code": "F20.9", "description": "Schizophrenia, unspecified", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["ptsd", "post-traumatic stress"], "code": "F43.10", "description": "Post-traumatic stress disorder, unspecified", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["alcohol dependence"], "code": "F10.20", "description": "Alcohol dependence, uncomplicated", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["opioid dependence"], "code": "F11.20", "description": "Opioid dependence, uncomplicated", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["tobacco dependence", "nicotine dependence", "smoker"], "code": "F17.210", "description": "Nicotine dependence, cigarettes, uncomplicated", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["insomnia"], "code": "G47.00", "description": "Insomnia, unspecified", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["dementia"], "code": "F03.90", "description": "Unspecified dementia without behavioral disturbance", "ref": "ICD-10-CM Ch. 5"},
    {"keywords": ["alzheimer"], "code": "G30.9", "description": "Alzheimer's disease, unspecified", "ref": "ICD-10-CM Ch. 6"},

    # Ch. 6 — Nervous system
    {"keywords": ["migraine"], "code": "G43.909", "description": "Migraine, unspecified, not intractable, without status migrainosus", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["headache"], "code": "R51.9", "description": "Headache, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["epilepsy", "seizure disorder"], "code": "G40.909", "description": "Epilepsy, unspecified, not intractable, without status epilepticus", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["parkinson"], "code": "G20", "description": "Parkinson's disease", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["multiple sclerosis", "ms disease"], "code": "G35", "description": "Multiple sclerosis", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["neuropathy"], "code": "G62.9", "description": "Polyneuropathy, unspecified", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["carpal tunnel"], "code": "G56.00", "description": "Carpal tunnel syndrome, unspecified upper limb", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["bell palsy"], "code": "G51.0", "description": "Bell's palsy", "ref": "ICD-10-CM Ch. 6"},

    # Ch. 7 — Eye / ear
    {"keywords": ["cataract"], "code": "H26.9", "description": "Unspecified cataract", "ref": "CMS NCD 80.10"},
    {"keywords": ["glaucoma"], "code": "H40.9", "description": "Unspecified glaucoma", "ref": "ICD-10-CM Ch. 7"},
    {"keywords": ["conjunctivitis"], "code": "H10.9", "description": "Unspecified conjunctivitis", "ref": "ICD-10-CM Ch. 7"},
    {"keywords": ["otitis media"], "code": "H66.90", "description": "Otitis media, unspecified, unspecified ear", "ref": "ICD-10-CM Ch. 8"},
    {"keywords": ["hearing loss"], "code": "H91.90", "description": "Unspecified hearing loss, unspecified ear", "ref": "ICD-10-CM Ch. 8"},

    # Ch. 9 — Circulatory
    {"keywords": ["hypertension", "high blood pressure", "htn"], "code": "I10", "description": "Essential (primary) hypertension", "ref": "ICD-10-CM Ch. 9 I.C.9.a"},
    {"keywords": ["hypertensive heart disease"], "code": "I11.9", "description": "Hypertensive heart disease without heart failure", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["hypertensive kidney disease"], "code": "I12.9", "description": "Hypertensive CKD with CKD stage 1-4", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["hypertensive emergency"], "code": "I16.1", "description": "Hypertensive emergency", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["acute myocardial infarction", "stemi", "ami", "heart attack"], "code": "I21.9", "description": "Acute myocardial infarction, unspecified", "ref": "CMS NCD 20.4 — AMI"},
    {"keywords": ["nstemi"], "code": "I21.4", "description": "Non-ST elevation (NSTEMI) myocardial infarction", "ref": "CMS NCD 20.4"},
    {"keywords": ["angina"], "code": "I20.9", "description": "Angina pectoris, unspecified", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["unstable angina"], "code": "I20.0", "description": "Unstable angina", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["coronary artery disease", "cad"], "code": "I25.10", "description": "Atherosclerotic heart disease of native coronary artery without angina", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["congestive heart failure", "chf", "heart failure"], "code": "I50.9", "description": "Heart failure, unspecified", "ref": "CMS LCD L34081"},
    {"keywords": ["systolic heart failure"], "code": "I50.20", "description": "Unspecified systolic (congestive) heart failure", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["diastolic heart failure"], "code": "I50.30", "description": "Unspecified diastolic (congestive) heart failure", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["atrial fibrillation", "a-fib", "afib"], "code": "I48.91", "description": "Unspecified atrial fibrillation", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["atrial flutter"], "code": "I48.92", "description": "Unspecified atrial flutter", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["svt", "supraventricular tachycardia"], "code": "I47.1", "description": "Supraventricular tachycardia", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["ventricular tachycardia"], "code": "I47.2", "description": "Ventricular tachycardia", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["bradycardia"], "code": "R00.1", "description": "Bradycardia, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["cerebrovascular accident", "stroke", "cva"], "code": "I63.9", "description": "Cerebral infarction, unspecified", "ref": "CMS NCD 160.14"},
    {"keywords": ["transient ischemic attack", "tia"], "code": "G45.9", "description": "Transient cerebral ischemic attack, unspecified", "ref": "ICD-10-CM Ch. 6"},
    {"keywords": ["intracerebral hemorrhage"], "code": "I61.9", "description": "Nontraumatic intracerebral hemorrhage, unspecified", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["dvt", "deep vein thrombosis"], "code": "I82.40", "description": "Acute embolism and thrombosis of unspecified deep veins of lower extremity", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["pulmonary embolism", "pe"], "code": "I26.99", "description": "Other pulmonary embolism without acute cor pulmonale", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["peripheral vascular disease", "pad"], "code": "I73.9", "description": "Peripheral vascular disease, unspecified", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["varicose veins"], "code": "I83.90", "description": "Asymptomatic varicose veins of unspecified lower extremity", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["cardiomyopathy"], "code": "I42.9", "description": "Cardiomyopathy, unspecified", "ref": "ICD-10-CM Ch. 9"},
    {"keywords": ["cardiac arrest"], "code": "I46.9", "description": "Cardiac arrest, cause unspecified", "ref": "ICD-10-CM Ch. 9"},

    # Ch. 10 — Respiratory
    {"keywords": ["chronic obstructive pulmonary disease", "copd"], "code": "J44.9", "description": "Chronic obstructive pulmonary disease, unspecified", "ref": "CMS LCD L33446"},
    {"keywords": ["copd exacerbation"], "code": "J44.1", "description": "COPD with (acute) exacerbation", "ref": "CMS LCD L33446"},
    {"keywords": ["asthma"], "code": "J45.909", "description": "Unspecified asthma, uncomplicated", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["asthma exacerbation"], "code": "J45.901", "description": "Unspecified asthma with (acute) exacerbation", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["pleural effusion"], "code": "J90", "description": "Pleural effusion, not elsewhere classified", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["pneumothorax"], "code": "J93.9", "description": "Pneumothorax, unspecified", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["respiratory failure", "hypoxic respiratory failure"], "code": "J96.00", "description": "Acute respiratory failure, unspecified whether with hypoxia or hypercapnia", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["bronchitis"], "code": "J40", "description": "Bronchitis, not specified as acute or chronic", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["sinusitis"], "code": "J32.9", "description": "Chronic sinusitis, unspecified", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["pharyngitis"], "code": "J02.9", "description": "Acute pharyngitis, unspecified", "ref": "ICD-10-CM Ch. 10"},
    {"keywords": ["obstructive sleep apnea", "osa"], "code": "G47.33", "description": "Obstructive sleep apnea (adult) (pediatric)", "ref": "CMS LCD L33800"},

    # Ch. 11 — Digestive
    {"keywords": ["gastroesophageal reflux", "gerd"], "code": "K21.9", "description": "Gastro-esophageal reflux disease without esophagitis", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["peptic ulcer"], "code": "K27.9", "description": "Peptic ulcer, site unspecified, unspecified as acute or chronic", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["gastritis"], "code": "K29.70", "description": "Gastritis, unspecified, without bleeding", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["appendicitis"], "code": "K35.80", "description": "Unspecified acute appendicitis", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["cholelithiasis", "gallstones"], "code": "K80.20", "description": "Calculus of gallbladder without cholecystitis, without obstruction", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["cholecystitis"], "code": "K81.9", "description": "Cholecystitis, unspecified", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["pancreatitis"], "code": "K85.90", "description": "Acute pancreatitis, unspecified, without necrosis or infection", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["diverticulitis"], "code": "K57.92", "description": "Diverticulitis of intestine, part unspecified, without perforation or abscess without bleeding", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["crohn"], "code": "K50.90", "description": "Crohn's disease, unspecified, without complications", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["ulcerative colitis"], "code": "K51.90", "description": "Ulcerative colitis, unspecified, without complications", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["irritable bowel", "ibs"], "code": "K58.9", "description": "Irritable bowel syndrome without diarrhea", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["constipation"], "code": "K59.00", "description": "Constipation, unspecified", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["diarrhea"], "code": "R19.7", "description": "Diarrhea, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["hernia", "inguinal hernia"], "code": "K40.90", "description": "Unilateral inguinal hernia without obstruction or gangrene", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["hemorrhoids"], "code": "K64.9", "description": "Unspecified hemorrhoids", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["cirrhosis"], "code": "K74.60", "description": "Unspecified cirrhosis of liver", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["fatty liver", "nash"], "code": "K76.0", "description": "Fatty (change of) liver, not elsewhere classified", "ref": "ICD-10-CM Ch. 11"},
    {"keywords": ["gi bleed", "gastrointestinal bleeding", "melena"], "code": "K92.2", "description": "Gastrointestinal hemorrhage, unspecified", "ref": "ICD-10-CM Ch. 11"},

    # Ch. 12 — Skin
    {"keywords": ["psoriasis"], "code": "L40.9", "description": "Psoriasis, unspecified", "ref": "ICD-10-CM Ch. 12"},
    {"keywords": ["eczema", "atopic dermatitis"], "code": "L20.9", "description": "Atopic dermatitis, unspecified", "ref": "ICD-10-CM Ch. 12"},
    {"keywords": ["pressure ulcer", "decubitus"], "code": "L89.90", "description": "Pressure ulcer of unspecified site, unspecified stage", "ref": "ICD-10-CM Ch. 12"},
    {"keywords": ["diabetic foot ulcer"], "code": "L97.509", "description": "Non-pressure chronic ulcer of other part of unspecified foot with unspecified severity", "ref": "ICD-10-CM Ch. 12"},
    {"keywords": ["abscess"], "code": "L02.91", "description": "Cutaneous abscess, unspecified", "ref": "ICD-10-CM Ch. 12"},

    # Ch. 13 — Musculoskeletal
    {"keywords": ["osteoarthritis"], "code": "M19.90", "description": "Unspecified osteoarthritis, unspecified site", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["rheumatoid arthritis"], "code": "M06.9", "description": "Rheumatoid arthritis, unspecified", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["gout"], "code": "M10.9", "description": "Gout, unspecified", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["back pain"], "code": "M54.9", "description": "Dorsalgia, unspecified", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["low back pain", "lumbago"], "code": "M54.50", "description": "Low back pain, unspecified", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["sciatica"], "code": "M54.30", "description": "Sciatica, unspecified side", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["disc herniation", "herniated disc"], "code": "M51.26", "description": "Other intervertebral disc displacement, lumbar region", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["rotator cuff"], "code": "M75.100", "description": "Unspecified rotator cuff tear, unspecified shoulder", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["knee pain"], "code": "M25.569", "description": "Pain in unspecified knee", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["osteoporosis"], "code": "M81.0", "description": "Age-related osteoporosis without current pathological fracture", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["tendonitis"], "code": "M77.9", "description": "Enthesopathy, unspecified", "ref": "ICD-10-CM Ch. 13"},
    {"keywords": ["bursitis"], "code": "M71.50", "description": "Other bursitis, not elsewhere classified, unspecified site", "ref": "ICD-10-CM Ch. 13"},

    # Ch. 14 — Genitourinary
    {"keywords": ["urinary tract infection", "uti"], "code": "N39.0", "description": "Urinary tract infection, site not specified", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["pyelonephritis"], "code": "N10", "description": "Acute pyelonephritis", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["acute kidney injury", "aki", "acute renal failure"], "code": "N17.9", "description": "Acute kidney failure, unspecified", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["chronic kidney disease", "ckd"], "code": "N18.9", "description": "Chronic kidney disease, unspecified", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["ckd stage 3"], "code": "N18.30", "description": "Chronic kidney disease, stage 3 unspecified", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["end stage renal disease", "esrd"], "code": "N18.6", "description": "End stage renal disease", "ref": "CMS NCD 230.18"},
    {"keywords": ["nephrolithiasis", "kidney stone"], "code": "N20.0", "description": "Calculus of kidney", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["urinary retention"], "code": "R33.9", "description": "Retention of urine, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["hematuria"], "code": "R31.9", "description": "Hematuria, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["benign prostatic hyperplasia", "bph"], "code": "N40.0", "description": "Benign prostatic hyperplasia without lower urinary tract symptoms", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["erectile dysfunction"], "code": "N52.9", "description": "Male erectile dysfunction, unspecified", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["menorrhagia"], "code": "N92.0", "description": "Excessive and frequent menstruation with regular cycle", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["endometriosis"], "code": "N80.9", "description": "Endometriosis, unspecified", "ref": "ICD-10-CM Ch. 14"},
    {"keywords": ["ovarian cyst"], "code": "N83.20", "description": "Unspecified ovarian cysts", "ref": "ICD-10-CM Ch. 14"},

    # Ch. 15 — Pregnancy
    {"keywords": ["pregnancy", "gestation"], "code": "Z33.1", "description": "Pregnant state, incidental", "ref": "ICD-10-CM Ch. 21"},
    {"keywords": ["preeclampsia"], "code": "O14.90", "description": "Unspecified pre-eclampsia, unspecified trimester", "ref": "ICD-10-CM Ch. 15"},
    {"keywords": ["gestational diabetes"], "code": "O24.410", "description": "Gestational diabetes mellitus in pregnancy, diet controlled", "ref": "ICD-10-CM Ch. 15"},

    # Ch. 17 — Congenital
    {"keywords": ["atrial septal defect", "asd"], "code": "Q21.1", "description": "Atrial septal defect", "ref": "ICD-10-CM Ch. 17"},
    {"keywords": ["ventricular septal defect", "vsd"], "code": "Q21.0", "description": "Ventricular septal defect", "ref": "ICD-10-CM Ch. 17"},

    # Ch. 18 — Symptoms, signs
    {"keywords": ["chest pain"], "code": "R07.9", "description": "Chest pain, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["shortness of breath", "dyspnea", "sob"], "code": "R06.02", "description": "Shortness of breath", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["cough"], "code": "R05.9", "description": "Cough, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["wheezing"], "code": "R06.2", "description": "Wheezing", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["abdominal pain"], "code": "R10.9", "description": "Unspecified abdominal pain", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["nausea"], "code": "R11.0", "description": "Nausea", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["vomiting"], "code": "R11.10", "description": "Vomiting, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["fever"], "code": "R50.9", "description": "Fever, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["syncope", "fainting"], "code": "R55", "description": "Syncope and collapse", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["dizziness", "vertigo"], "code": "R42", "description": "Dizziness and giddiness", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["fatigue"], "code": "R53.83", "description": "Other fatigue", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["weight loss"], "code": "R63.4", "description": "Abnormal weight loss", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["altered mental status", "ams", "confusion"], "code": "R41.82", "description": "Altered mental status, unspecified", "ref": "ICD-10-CM Ch. 18"},
    {"keywords": ["hyponatremia"], "code": "E87.1", "description": "Hyponatremia", "ref": "ICD-10-CM Ch. 4"},
    {"keywords": ["leukocytosis"], "code": "D72.829", "description": "Elevated white blood cell count, unspecified", "ref": "ICD-10-CM Ch. 3"},
    {"keywords": ["shock"], "code": "R57.9", "description": "Shock, unspecified", "ref": "ICD-10-CM Ch. 18"},

    # Ch. 19 — Injury, poisoning
    {"keywords": ["fracture femur", "femur fracture"], "code": "S72.90XA", "description": "Unspecified fracture of unspecified femur, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["fracture hip", "hip fracture"], "code": "S72.009A", "description": "Fracture of unspecified part of neck of unspecified femur", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["fracture tibia"], "code": "S82.209A", "description": "Unspecified fracture of shaft of unspecified tibia, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["fracture wrist"], "code": "S62.109A", "description": "Unspecified fracture of navicular bone of unspecified wrist, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["fracture ankle"], "code": "S82.899A", "description": "Other fracture of unspecified lower leg, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["concussion"], "code": "S06.0X0A", "description": "Concussion without loss of consciousness, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["traumatic brain injury", "tbi"], "code": "S06.9X0A", "description": "Unspecified intracranial injury without loss of consciousness, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["laceration"], "code": "T14.8XXA", "description": "Other injury of unspecified body region, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["burn"], "code": "T30.0", "description": "Burn of unspecified body region, unspecified degree", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["sprain ankle"], "code": "S93.409A", "description": "Sprain of unspecified ligament of unspecified ankle, initial encounter", "ref": "ICD-10-CM Ch. 19"},
    {"keywords": ["motor vehicle accident", "mva"], "code": "V89.2XXA", "description": "Person injured in unspecified motor-vehicle accident, traffic, initial encounter", "ref": "ICD-10-CM Ch. 20"},
    {"keywords": ["overdose"], "code": "T50.901A", "description": "Poisoning by unspecified drugs, accidental, initial encounter", "ref": "ICD-10-CM Ch. 19"},

    # Ch. 21 — Z codes / status
    {"keywords": ["routine health examination", "annual wellness", "awv"], "code": "Z00.00", "description": "Encounter for general adult medical examination without abnormal findings", "ref": "CMS IOM 100-04 Ch. 12"},
    {"keywords": ["long-term anticoagulant use"], "code": "Z79.01", "description": "Long term (current) use of anticoagulants", "ref": "ICD-10-CM Ch. 21"},
    {"keywords": ["long-term insulin use"], "code": "Z79.4", "description": "Long term (current) use of insulin", "ref": "ICD-10-CM Ch. 21"},
    {"keywords": ["dialysis", "on dialysis"], "code": "Z99.2", "description": "Dependence on renal dialysis", "ref": "CMS NCD 230.18"},
    {"keywords": ["pacemaker"], "code": "Z95.0", "description": "Presence of cardiac pacemaker", "ref": "ICD-10-CM Ch. 21"},
    {"keywords": ["colonoscopy screening"], "code": "Z12.11", "description": "Encounter for screening for malignant neoplasm of colon", "ref": "CMS NCD 210.3"},
    {"keywords": ["mammogram screening"], "code": "Z12.31", "description": "Encounter for screening mammogram for malignant neoplasm of breast", "ref": "CMS NCD 220.4"},
]

# --------------------------------------------------------------------------
# ICD-10-PCS (procedures, UB-04 inpatient) — ~40 entries
# --------------------------------------------------------------------------
ICD10_PCS: List[dict] = [
    {"keywords": ["appendectomy"], "code": "0DTJ4ZZ", "description": "Resection of Appendix, Percutaneous Endoscopic", "ref": "ICD-10-PCS B3"},
    {"keywords": ["cholecystectomy"], "code": "0FT44ZZ", "description": "Resection of Gallbladder, Percutaneous Endoscopic", "ref": "ICD-10-PCS B3"},
    {"keywords": ["coronary artery bypass", "cabg"], "code": "021209W", "description": "Bypass Coronary Artery, Two Arteries", "ref": "ICD-10-PCS B3.6a"},
    {"keywords": ["cesarean", "c-section"], "code": "10D00Z1", "description": "Extraction of Products of Conception, Low, Open", "ref": "ICD-10-PCS Ch. Obstetrics"},
    {"keywords": ["hip replacement"], "code": "0SR9019", "description": "Replacement of Right Hip Joint, Metal on Polyethylene, Open", "ref": "ICD-10-PCS B3"},
    {"keywords": ["knee replacement"], "code": "0SRC0J9", "description": "Replacement of Left Knee Joint, Synthetic Substitute, Open", "ref": "ICD-10-PCS B3"},
    {"keywords": ["hysterectomy"], "code": "0UT90ZZ", "description": "Resection of Uterus, Open Approach", "ref": "ICD-10-PCS B3"},
    {"keywords": ["mastectomy"], "code": "0HTT0ZZ", "description": "Resection of Right Breast, Open Approach", "ref": "ICD-10-PCS B3"},
    {"keywords": ["percutaneous coronary intervention", "pci", "angioplasty coronary"], "code": "02703ZZ", "description": "Dilation of Coronary Artery, One Site, Percutaneous", "ref": "ICD-10-PCS B3"},
    {"keywords": ["pacemaker insertion"], "code": "0JH605Z", "description": "Insertion of Cardiac Rhythm Related Device into Chest Subcutaneous Tissue and Fascia, Open Approach", "ref": "ICD-10-PCS B3"},
    {"keywords": ["colectomy"], "code": "0DTE0ZZ", "description": "Resection of Large Intestine, Open Approach", "ref": "ICD-10-PCS B3"},
    {"keywords": ["mechanical ventilation < 24"], "code": "5A1935Z", "description": "Respiratory Ventilation, Less than 24 Consecutive Hours", "ref": "ICD-10-PCS Ch. 5A"},
    {"keywords": ["mechanical ventilation 24-96"], "code": "5A1945Z", "description": "Respiratory Ventilation, 24-96 Consecutive Hours", "ref": "ICD-10-PCS Ch. 5A"},
    {"keywords": ["mechanical ventilation >96"], "code": "5A1955Z", "description": "Respiratory Ventilation, Greater than 96 Consecutive Hours", "ref": "ICD-10-PCS Ch. 5A"},
    {"keywords": ["hemodialysis"], "code": "5A1D00Z", "description": "Performance of Urinary Filtration, Single", "ref": "CMS NCD 230.18"},
    {"keywords": ["lumbar fusion"], "code": "0SG0070", "description": "Fusion of Lumbar Vertebral Joint with Autologous Tissue Substitute, Anterior Approach", "ref": "CMS NCD 150.10"},
]

# --------------------------------------------------------------------------
# CPT — ~150 entries
# --------------------------------------------------------------------------
CPT_CODES: List[dict] = [
    # Evaluation & Management
    {"keywords": ["office visit established", "established patient"], "code": "99213", "description": "Office/outpatient visit, established patient, low MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["office visit moderate established"], "code": "99214", "description": "Office visit, established, moderate MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["office visit high established"], "code": "99215", "description": "Office visit, established, high MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["office visit new"], "code": "99203", "description": "Office visit, new patient, low MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["office visit new moderate"], "code": "99204", "description": "Office visit, new patient, moderate MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["office visit new high"], "code": "99205", "description": "Office visit, new patient, high MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["ed visit level 3"], "code": "99283", "description": "Emergency department visit, moderate severity, moderate MDM", "ref": "AMA CPT E/M"},
    {"keywords": ["ed visit level 4", "emergency department moderate"], "code": "99284", "description": "Emergency department visit, moderate/high severity", "ref": "AMA CPT E/M"},
    {"keywords": ["ed visit level 5", "emergency department high"], "code": "99285", "description": "Emergency department visit, high severity", "ref": "AMA CPT E/M"},
    {"keywords": ["initial hospital care low"], "code": "99221", "description": "Initial hospital inpatient, low complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["initial hospital care moderate"], "code": "99222", "description": "Initial hospital inpatient, moderate complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["initial hospital care", "admission h&p"], "code": "99223", "description": "Initial hospital inpatient, high complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["subsequent hospital low"], "code": "99231", "description": "Subsequent hospital care, low complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["subsequent hospital care"], "code": "99232", "description": "Subsequent hospital care, moderate complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["subsequent hospital high"], "code": "99233", "description": "Subsequent hospital care, high complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["discharge 30"], "code": "99238", "description": "Hospital discharge day management, ≤30 min", "ref": "AMA CPT E/M"},
    {"keywords": ["discharge"], "code": "99239", "description": "Hospital discharge day management, >30 min", "ref": "AMA CPT E/M"},
    {"keywords": ["observation initial"], "code": "99219", "description": "Initial observation care, moderate complexity", "ref": "AMA CPT E/M"},
    {"keywords": ["critical care"], "code": "99291", "description": "Critical care, first 30-74 minutes", "ref": "AMA CPT E/M"},
    {"keywords": ["critical care additional"], "code": "99292", "description": "Critical care, each additional 30 min", "ref": "AMA CPT E/M"},
    {"keywords": ["preventive visit adult"], "code": "99396", "description": "Periodic comprehensive preventive medicine reevaluation, 40-64 years", "ref": "AMA CPT Preventive"},
    {"keywords": ["telehealth visit"], "code": "99441", "description": "Telephone E/M service, 5-10 min", "ref": "CMS Telehealth IFR"},
    {"keywords": ["care management chronic"], "code": "99490", "description": "Chronic care management, first 20 min", "ref": "CMS MLN CCM"},

    # Radiology
    {"keywords": ["chest x-ray", "chest xray", "cxr"], "code": "71046", "description": "Radiologic exam, chest, 2 views", "ref": "AMA CPT Radiology"},
    {"keywords": ["chest x-ray single"], "code": "71045", "description": "Radiologic exam, chest, single view", "ref": "AMA CPT Radiology"},
    {"keywords": ["abdominal x-ray"], "code": "74018", "description": "Radiologic exam, abdomen, single view", "ref": "AMA CPT Radiology"},
    {"keywords": ["ct head", "head ct"], "code": "70450", "description": "CT head or brain without contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["ct head with contrast"], "code": "70460", "description": "CT head or brain with contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["ct chest"], "code": "71250", "description": "CT thorax without contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["ct chest with contrast"], "code": "71260", "description": "CT thorax with contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["ct abdomen pelvis"], "code": "74177", "description": "CT abdomen & pelvis with contrast", "ref": "CMS NCD 220.1"},
    {"keywords": ["ct pulmonary angiogram", "ctpa"], "code": "71275", "description": "CTA chest (non-coronary) with contrast", "ref": "CMS LCD L33569"},
    {"keywords": ["mri brain"], "code": "70551", "description": "MRI brain without contrast", "ref": "CMS NCD 220.2"},
    {"keywords": ["mri brain with contrast"], "code": "70553", "description": "MRI brain without and with contrast", "ref": "CMS NCD 220.2"},
    {"keywords": ["mri lumbar"], "code": "72148", "description": "MRI lumbar spine without contrast", "ref": "CMS LCD L34007"},
    {"keywords": ["mri knee"], "code": "73721", "description": "MRI lower extremity joint without contrast", "ref": "CMS LCD L34007"},
    {"keywords": ["ultrasound abdomen"], "code": "76700", "description": "Ultrasound, abdominal, real time, complete", "ref": "AMA CPT Radiology"},
    {"keywords": ["ultrasound obstetric"], "code": "76805", "description": "Ultrasound, pregnant uterus, after first trimester, complete", "ref": "AMA CPT Radiology"},
    {"keywords": ["mammogram screening"], "code": "77067", "description": "Screening mammography, bilateral", "ref": "CMS NCD 220.4"},
    {"keywords": ["mammogram diagnostic"], "code": "77066", "description": "Diagnostic mammography, bilateral", "ref": "CMS NCD 220.4"},
    {"keywords": ["dexa bone density"], "code": "77080", "description": "DXA bone density study, axial skeleton", "ref": "CMS NCD 150.3"},

    # Cardiology procedures
    {"keywords": ["ekg", "ecg", "electrocardiogram"], "code": "93000", "description": "Electrocardiogram, routine ECG with 12 leads", "ref": "CMS LCD L33950"},
    {"keywords": ["echocardiogram", "echo"], "code": "93306", "description": "Echocardiography, transthoracic, complete", "ref": "CMS LCD L33630"},
    {"keywords": ["stress test", "treadmill"], "code": "93017", "description": "Cardiovascular stress test, tracing only", "ref": "AMA CPT Cardiology"},
    {"keywords": ["cardiac catheterization"], "code": "93458", "description": "Cardiac cath, left heart, coronary angiography", "ref": "CMS NCD 20.4"},
    {"keywords": ["pacemaker insertion procedure"], "code": "33208", "description": "Insertion of permanent pacemaker, dual chamber", "ref": "CMS NCD 20.8"},
    {"keywords": ["cardioversion"], "code": "92960", "description": "Cardioversion, elective, external", "ref": "AMA CPT Cardiology"},
    {"keywords": ["holter monitor"], "code": "93224", "description": "External Holter monitoring up to 48 hours", "ref": "AMA CPT Cardiology"},
    {"keywords": ["arterial line"], "code": "36620", "description": "Arterial catheterization, percutaneous", "ref": "AMA CPT Medicine"},

    # Pulmonary / respiratory
    {"keywords": ["pulmonary function test", "pft"], "code": "94010", "description": "Spirometry", "ref": "CMS LCD L33568"},
    {"keywords": ["nebulizer treatment"], "code": "94640", "description": "Pressurized/nonpressurized inhalation treatment", "ref": "AMA CPT Medicine"},
    {"keywords": ["intubation"], "code": "31500", "description": "Intubation, endotracheal, emergency procedure", "ref": "AMA CPT Surgery"},
    {"keywords": ["bronchoscopy"], "code": "31622", "description": "Bronchoscopy, diagnostic, with cell washing", "ref": "AMA CPT Surgery"},

    # Lab
    {"keywords": ["complete blood count", "cbc"], "code": "85025", "description": "CBC with automated differential", "ref": "CMS Lab NCD 190.15"},
    {"keywords": ["cbc without differential"], "code": "85027", "description": "CBC, automated, complete without differential", "ref": "CMS Lab NCD 190.15"},
    {"keywords": ["basic metabolic panel", "bmp"], "code": "80048", "description": "Basic metabolic panel", "ref": "CMS Lab NCD 190.14"},
    {"keywords": ["comprehensive metabolic panel", "cmp"], "code": "80053", "description": "Comprehensive metabolic panel", "ref": "CMS Lab NCD 190.14"},
    {"keywords": ["lipid panel"], "code": "80061", "description": "Lipid panel", "ref": "CMS NCD 190.23"},
    {"keywords": ["hemoglobin a1c", "hba1c", "a1c"], "code": "83036", "description": "Glycated hemoglobin (A1C)", "ref": "CMS NCD 190.21"},
    {"keywords": ["tsh", "thyroid stimulating hormone"], "code": "84443", "description": "Thyroid stimulating hormone", "ref": "CMS NCD 190.22"},
    {"keywords": ["urinalysis"], "code": "81003", "description": "Urinalysis by dipstick, automated", "ref": "AMA CPT Pathology"},
    {"keywords": ["urine culture"], "code": "87086", "description": "Culture, bacterial; urine, quantitative", "ref": "AMA CPT Pathology"},
    {"keywords": ["blood culture"], "code": "87040", "description": "Culture, bacterial; blood, aerobic", "ref": "AMA CPT Pathology"},
    {"keywords": ["strep test"], "code": "87880", "description": "Streptococcus, group A, direct optical observation", "ref": "AMA CPT Pathology"},
    {"keywords": ["influenza test"], "code": "87804", "description": "Infectious agent antigen detection; influenza", "ref": "AMA CPT Pathology"},
    {"keywords": ["covid pcr"], "code": "87635", "description": "Infectious agent by nucleic acid, SARS-CoV-2", "ref": "CMS COVID-19 Coding"},
    {"keywords": ["troponin"], "code": "84484", "description": "Troponin, quantitative", "ref": "CMS LCD L34539"},
    {"keywords": ["bnp"], "code": "83880", "description": "Natriuretic peptide", "ref": "CMS LCD L33831"},
    {"keywords": ["psa"], "code": "84153", "description": "Prostate specific antigen, total", "ref": "CMS NCD 210.1"},
    {"keywords": ["d-dimer", "d dimer"], "code": "85379", "description": "Fibrin degradation products, D-dimer, quantitative", "ref": "CMS LCD L33794"},
    {"keywords": ["pt inr", "prothrombin"], "code": "85610", "description": "Prothrombin time (PT)", "ref": "CMS NCD 190.11"},
    {"keywords": ["ptt"], "code": "85730", "description": "Thromboplastin time, partial (PTT)", "ref": "CMS NCD 190.16"},
    {"keywords": ["culture stool"], "code": "87045", "description": "Culture, stool; salmonella/shigella", "ref": "AMA CPT Pathology"},

    # Surgery — general
    {"keywords": ["appendectomy"], "code": "44970", "description": "Laparoscopic appendectomy", "ref": "AMA CPT Surgery"},
    {"keywords": ["cholecystectomy"], "code": "47562", "description": "Laparoscopic cholecystectomy", "ref": "AMA CPT Surgery"},
    {"keywords": ["inguinal hernia repair"], "code": "49505", "description": "Repair, initial inguinal hernia, age 5+, reducible", "ref": "AMA CPT Surgery"},
    {"keywords": ["lap hernia repair"], "code": "49650", "description": "Laparoscopy, surgical; repair initial inguinal hernia", "ref": "AMA CPT Surgery"},
    {"keywords": ["colonoscopy"], "code": "45378", "description": "Colonoscopy, flexible, diagnostic", "ref": "CMS NCD 210.3"},
    {"keywords": ["colonoscopy with biopsy"], "code": "45380", "description": "Colonoscopy, flexible; with biopsy", "ref": "CMS NCD 210.3"},
    {"keywords": ["colonoscopy with polypectomy"], "code": "45385", "description": "Colonoscopy with polyp removal by snare", "ref": "CMS NCD 210.3"},
    {"keywords": ["upper endoscopy", "egd"], "code": "43235", "description": "Esophagogastroduodenoscopy, diagnostic", "ref": "AMA CPT Surgery"},
    {"keywords": ["egd with biopsy"], "code": "43239", "description": "EGD, flexible; with biopsy", "ref": "AMA CPT Surgery"},
    {"keywords": ["tonsillectomy"], "code": "42820", "description": "Tonsillectomy and adenoidectomy; younger than age 12", "ref": "AMA CPT Surgery"},
    {"keywords": ["hysterectomy total"], "code": "58150", "description": "Total abdominal hysterectomy", "ref": "AMA CPT Surgery"},
    {"keywords": ["cesarean delivery"], "code": "59510", "description": "Routine obstetric care incl. antepartum, cesarean delivery", "ref": "AMA CPT Surgery"},
    {"keywords": ["vaginal delivery"], "code": "59400", "description": "Routine obstetric care incl. antepartum, vaginal delivery", "ref": "AMA CPT Surgery"},
    {"keywords": ["mastectomy lumpectomy"], "code": "19301", "description": "Mastectomy, partial (lumpectomy)", "ref": "AMA CPT Surgery"},
    {"keywords": ["thyroidectomy"], "code": "60240", "description": "Thyroidectomy, total or complete", "ref": "AMA CPT Surgery"},

    # Orthopedics
    {"keywords": ["total knee arthroplasty", "tka"], "code": "27447", "description": "Arthroplasty, knee, condyle and plateau; total knee", "ref": "CMS LCD L37525"},
    {"keywords": ["total hip arthroplasty", "tha"], "code": "27130", "description": "Arthroplasty, acetabular and proximal femoral prosthetic replacement", "ref": "CMS LCD L37525"},
    {"keywords": ["rotator cuff repair"], "code": "23412", "description": "Repair of ruptured rotator cuff, chronic", "ref": "AMA CPT Surgery"},
    {"keywords": ["acl repair", "acl reconstruction"], "code": "29888", "description": "Arthroscopic anterior cruciate ligament repair/reconstruction", "ref": "AMA CPT Surgery"},
    {"keywords": ["meniscectomy"], "code": "29881", "description": "Arthroscopy, knee, surgical; with meniscectomy (medial or lateral)", "ref": "AMA CPT Surgery"},
    {"keywords": ["closed reduction fracture"], "code": "25605", "description": "Closed treatment of distal radius fracture, with manipulation", "ref": "AMA CPT Surgery"},
    {"keywords": ["joint injection knee"], "code": "20610", "description": "Arthrocentesis/injection, major joint or bursa", "ref": "CMS LCD L35010"},
    {"keywords": ["trigger finger injection"], "code": "20550", "description": "Injection, single tendon sheath or ligament", "ref": "AMA CPT Surgery"},

    # OB/GYN
    {"keywords": ["pap smear"], "code": "88175", "description": "Cytopathology, cervical or vaginal, auto screen", "ref": "CMS NCD 210.2"},
    {"keywords": ["iud insertion"], "code": "58300", "description": "Insertion of intrauterine device (IUD)", "ref": "AMA CPT Surgery"},
    {"keywords": ["endometrial biopsy"], "code": "58100", "description": "Endometrial sampling with or without endocervical sampling", "ref": "AMA CPT Surgery"},

    # Neurology
    {"keywords": ["lumbar puncture"], "code": "62270", "description": "Spinal puncture, lumbar, diagnostic", "ref": "AMA CPT Surgery"},
    {"keywords": ["eeg"], "code": "95816", "description": "EEG, recording awake and drowsy", "ref": "AMA CPT Medicine"},
    {"keywords": ["emg"], "code": "95886", "description": "Needle electromyography, complete study", "ref": "AMA CPT Medicine"},

    # Ophthalmology
    {"keywords": ["cataract extraction"], "code": "66984", "description": "Extracapsular cataract extraction with insertion of IOL", "ref": "CMS NCD 80.10"},

    # Minor procedures
    {"keywords": ["skin biopsy"], "code": "11102", "description": "Tangential biopsy of skin", "ref": "AMA CPT Surgery"},
    {"keywords": ["excision benign lesion"], "code": "11400", "description": "Excision, benign lesion, trunk/arms/legs; 0.5 cm or less", "ref": "AMA CPT Surgery"},
    {"keywords": ["simple repair laceration"], "code": "12001", "description": "Simple repair of superficial wounds; 2.5 cm or less", "ref": "AMA CPT Surgery"},
    {"keywords": ["suture removal"], "code": "15851", "description": "Removal of sutures under anesthesia", "ref": "AMA CPT Surgery"},
    {"keywords": ["foley catheter"], "code": "51702", "description": "Insertion of temporary indwelling bladder catheter; simple", "ref": "AMA CPT Surgery"},
    {"keywords": ["central line"], "code": "36556", "description": "Insertion of non-tunneled centrally inserted CVC; age 5+", "ref": "AMA CPT Surgery"},
    {"keywords": ["thoracentesis"], "code": "32554", "description": "Thoracentesis, without imaging guidance", "ref": "AMA CPT Surgery"},
    {"keywords": ["paracentesis"], "code": "49082", "description": "Abdominal paracentesis without imaging guidance", "ref": "AMA CPT Surgery"},

    # Therapy
    {"keywords": ["physical therapy evaluation", "pt eval"], "code": "97161", "description": "PT evaluation, low complexity", "ref": "CMS LCD L33631"},
    {"keywords": ["physical therapy moderate"], "code": "97162", "description": "PT evaluation, moderate complexity", "ref": "CMS LCD L33631"},
    {"keywords": ["physical therapy high"], "code": "97163", "description": "PT evaluation, high complexity", "ref": "CMS LCD L33631"},
    {"keywords": ["therapeutic exercise"], "code": "97110", "description": "Therapeutic exercises, each 15 min", "ref": "CMS LCD L33631"},
    {"keywords": ["manual therapy"], "code": "97140", "description": "Manual therapy techniques, each 15 min", "ref": "CMS LCD L33631"},
    {"keywords": ["occupational therapy eval"], "code": "97165", "description": "OT evaluation, low complexity", "ref": "CMS LCD L33631"},
    {"keywords": ["speech therapy eval"], "code": "92523", "description": "Evaluation of speech sound production with language", "ref": "CMS LCD L35070"},

    # Vaccines
    {"keywords": ["flu shot", "influenza vaccine"], "code": "90686", "description": "Influenza virus vaccine, quadrivalent, IM", "ref": "CMS MLN Vaccines"},
    {"keywords": ["pneumococcal vaccine"], "code": "90670", "description": "Pneumococcal conjugate vaccine 13-valent, IM", "ref": "CMS MLN Vaccines"},
    {"keywords": ["hepatitis b vaccine"], "code": "90746", "description": "Hepatitis B vaccine, adult dosage, IM", "ref": "CMS MLN Vaccines"},
    {"keywords": ["tdap vaccine"], "code": "90715", "description": "Tdap vaccine, 7+ years, IM", "ref": "CMS MLN Vaccines"},
    {"keywords": ["covid vaccine admin"], "code": "91318", "description": "SARS-CoV-2 mRNA vaccine administration", "ref": "CMS MLN MM12439"},
    {"keywords": ["vaccine admin single"], "code": "90471", "description": "Immunization administration; single vaccine", "ref": "AMA CPT Medicine"},
    {"keywords": ["vaccine admin additional"], "code": "90472", "description": "Immunization admin; each additional vaccine", "ref": "AMA CPT Medicine"},

    # Anesthesia (sample)
    {"keywords": ["anesthesia abdomen"], "code": "00790", "description": "Anesthesia for intraperitoneal procedures upper abdomen", "ref": "ASA Anesthesia"},
    {"keywords": ["anesthesia knee"], "code": "01400", "description": "Anesthesia for open or surgical arthroscopic procedures on knee joint", "ref": "ASA Anesthesia"},

    # Psychiatry
    {"keywords": ["psychiatric diagnostic eval"], "code": "90791", "description": "Psychiatric diagnostic evaluation", "ref": "AMA CPT Psychiatry"},
    {"keywords": ["psychotherapy 45"], "code": "90834", "description": "Psychotherapy, 45 minutes", "ref": "AMA CPT Psychiatry"},
    {"keywords": ["psychotherapy 60"], "code": "90837", "description": "Psychotherapy, 60 minutes", "ref": "AMA CPT Psychiatry"},

    # Dialysis / Nephrology
    {"keywords": ["hemodialysis management"], "code": "90935", "description": "Hemodialysis procedure with single evaluation", "ref": "CMS NCD 230.18"},
    {"keywords": ["peritoneal dialysis"], "code": "90945", "description": "Dialysis procedure other than hemodialysis with single eval", "ref": "CMS NCD 230.18"},
]

# --------------------------------------------------------------------------
# HCPCS Level II — ~60 entries
# --------------------------------------------------------------------------
HCPCS_CODES: List[dict] = [
    {"keywords": ["ambulance basic life support", "bls"], "code": "A0428", "description": "Ambulance service, BLS, non-emergency", "ref": "CMS Ambulance Fee Schedule"},
    {"keywords": ["ambulance bls emergency"], "code": "A0429", "description": "Ambulance service, BLS, emergency", "ref": "CMS Ambulance Fee Schedule"},
    {"keywords": ["ambulance advanced life support", "als"], "code": "A0427", "description": "Ambulance service, ALS, emergency, Level 1", "ref": "CMS Ambulance Fee Schedule"},
    {"keywords": ["ambulance mileage"], "code": "A0425", "description": "Ground mileage, per statute mile", "ref": "CMS Ambulance Fee Schedule"},
    {"keywords": ["oxygen", "home oxygen"], "code": "E1390", "description": "Oxygen concentrator, single delivery port", "ref": "CMS DMEPOS LCD L33797"},
    {"keywords": ["portable oxygen"], "code": "E0431", "description": "Portable gaseous oxygen system, rental", "ref": "CMS DMEPOS LCD L33797"},
    {"keywords": ["cpap"], "code": "E0601", "description": "Continuous positive airway pressure device", "ref": "CMS LCD L33800"},
    {"keywords": ["bipap"], "code": "E0470", "description": "Respiratory assist device, bilevel without backup rate", "ref": "CMS LCD L33800"},
    {"keywords": ["wheelchair manual"], "code": "E1130", "description": "Standard wheelchair", "ref": "CMS DMEPOS"},
    {"keywords": ["power wheelchair"], "code": "K0823", "description": "Power wheelchair, group 2 standard, captain's chair", "ref": "CMS LCD L33789"},
    {"keywords": ["walker", "standard walker"], "code": "E0143", "description": "Walker, folding, wheeled, adjustable", "ref": "CMS DMEPOS"},
    {"keywords": ["cane"], "code": "E0100", "description": "Cane, includes canes of all materials, with tips", "ref": "CMS DMEPOS"},
    {"keywords": ["hospital bed"], "code": "E0260", "description": "Hospital bed, semi-electric", "ref": "CMS DMEPOS"},
    {"keywords": ["commode"], "code": "E0163", "description": "Commode chair, stationary", "ref": "CMS DMEPOS"},
    {"keywords": ["tens unit"], "code": "E0720", "description": "TENS unit, two lead, localized stimulation", "ref": "CMS DMEPOS"},
    {"keywords": ["enteral nutrition"], "code": "B4150", "description": "Enteral formula, nutritionally complete, 100 calories = 1 unit", "ref": "CMS LCD L33783"},
    {"keywords": ["ostomy pouch"], "code": "A5051", "description": "Pouch, closed; with barrier, 1-piece", "ref": "CMS DMEPOS"},
    {"keywords": ["diabetic test strips"], "code": "A4253", "description": "Blood glucose test or reagent strips, per 50 strips", "ref": "CMS DMEPOS"},
    {"keywords": ["insulin"], "code": "J1815", "description": "Injection, insulin, per 5 units", "ref": "CMS Part B Drug File"},
    {"keywords": ["insulin pump supplies"], "code": "A4230", "description": "Infusion set for external insulin pump, non-needle", "ref": "CMS DMEPOS"},
    {"keywords": ["epinephrine injection"], "code": "J0171", "description": "Injection, adrenalin, 0.1 mg", "ref": "CMS Part B Drug File"},
    {"keywords": ["albuterol inhalation"], "code": "J7613", "description": "Albuterol, inhalation solution, 1 mg", "ref": "CMS Part B Drug File"},
    {"keywords": ["iv solution"], "code": "J7030", "description": "Infusion, normal saline solution, 1000 cc", "ref": "CMS Part B Drug File"},
    {"keywords": ["furosemide injection"], "code": "J1940", "description": "Injection, furosemide, up to 20 mg", "ref": "CMS Part B Drug File"},
    {"keywords": ["morphine injection"], "code": "J2270", "description": "Injection, morphine sulfate, up to 10 mg", "ref": "CMS Part B Drug File"},
    {"keywords": ["ondansetron injection"], "code": "J2405", "description": "Injection, ondansetron HCl, per 1 mg", "ref": "CMS Part B Drug File"},
    {"keywords": ["iv push"], "code": "J3490", "description": "Unclassified drugs (J-code)", "ref": "CMS Part B Drug File"},
    {"keywords": ["rituximab"], "code": "J9312", "description": "Injection, rituximab, 10 mg", "ref": "CMS LCD L33394"},
    {"keywords": ["trastuzumab"], "code": "J9355", "description": "Injection, trastuzumab, excluding biosimilar, 10 mg", "ref": "CMS Part B Drug File"},
    {"keywords": ["covid vaccine pfizer"], "code": "91300", "description": "SARS-CoV-2 vaccine, mRNA-LNP, Pfizer", "ref": "CMS MLN MM12439"},
    {"keywords": ["skilled nursing visit"], "code": "G0154", "description": "Services performed by a skilled nurse in home health setting, each 15 min", "ref": "CMS Home Health PPS"},
    {"keywords": ["home health aide visit"], "code": "G0156", "description": "Services of home health/hospice aide in home health setting, each 15 min", "ref": "CMS Home Health PPS"},
    {"keywords": ["awv initial"], "code": "G0438", "description": "Annual wellness visit; initial", "ref": "CMS IOM 100-04 Ch. 12"},
    {"keywords": ["awv subsequent"], "code": "G0439", "description": "Annual wellness visit; subsequent", "ref": "CMS IOM 100-04 Ch. 12"},
]

# --------------------------------------------------------------------------
# Revenue codes (UB-04) — NUBC
# --------------------------------------------------------------------------
REVENUE_CODES: List[dict] = [
    {"keywords": ["room and board", "semi-private"], "code": "0120", "description": "Room & Board – Semi-Private", "ref": "NUBC UB-04"},
    {"keywords": ["private room"], "code": "0110", "description": "Room & Board – Private (1 bed)", "ref": "NUBC UB-04"},
    {"keywords": ["ward", "4+ beds"], "code": "0130", "description": "Room & Board – Ward", "ref": "NUBC UB-04"},
    {"keywords": ["icu", "intensive care"], "code": "0200", "description": "Intensive Care Unit – General", "ref": "NUBC UB-04"},
    {"keywords": ["ccu", "cardiac care"], "code": "0210", "description": "Coronary Care Unit – General", "ref": "NUBC UB-04"},
    {"keywords": ["nursery"], "code": "0170", "description": "Nursery – General", "ref": "NUBC UB-04"},
    {"keywords": ["neonatal icu", "nicu"], "code": "0174", "description": "Nursery – NICU", "ref": "NUBC UB-04"},
    {"keywords": ["emergency room", " ed ", " er "], "code": "0450", "description": "Emergency Room – General", "ref": "NUBC UB-04"},
    {"keywords": ["observation"], "code": "0762", "description": "Observation Room", "ref": "NUBC UB-04"},
    {"keywords": ["operating room", "or ", "surgery suite"], "code": "0360", "description": "Operating Room Services – General", "ref": "NUBC UB-04"},
    {"keywords": ["recovery room", "pacu"], "code": "0710", "description": "Recovery Room – General", "ref": "NUBC UB-04"},
    {"keywords": ["anesthesia"], "code": "0370", "description": "Anesthesia – General", "ref": "NUBC UB-04"},
    {"keywords": ["labor delivery", "labor room"], "code": "0720", "description": "Labor Room / Delivery – General", "ref": "NUBC UB-04"},
    {"keywords": ["laboratory", " lab "], "code": "0300", "description": "Laboratory – General", "ref": "NUBC UB-04"},
    {"keywords": ["pathology"], "code": "0310", "description": "Laboratory Pathology – General", "ref": "NUBC UB-04"},
    {"keywords": ["radiology", "imaging", "x-ray"], "code": "0320", "description": "Diagnostic Radiology – General", "ref": "NUBC UB-04"},
    {"keywords": ["ct scan revenue"], "code": "0350", "description": "CT Scan – General", "ref": "NUBC UB-04"},
    {"keywords": ["mri revenue"], "code": "0610", "description": "MRI / MRS – General", "ref": "NUBC UB-04"},
    {"keywords": ["nuclear medicine"], "code": "0340", "description": "Nuclear Medicine – General", "ref": "NUBC UB-04"},
    {"keywords": ["pharmacy", "medication"], "code": "0250", "description": "Pharmacy – General", "ref": "NUBC UB-04"},
    {"keywords": ["iv therapy"], "code": "0260", "description": "IV Therapy – General", "ref": "NUBC UB-04"},
    {"keywords": ["blood products"], "code": "0380", "description": "Blood – General", "ref": "NUBC UB-04"},
    {"keywords": ["respiratory therapy", "ventilator"], "code": "0410", "description": "Respiratory Services – General", "ref": "NUBC UB-04"},
    {"keywords": ["physical therapy charge"], "code": "0420", "description": "Physical Therapy – General", "ref": "NUBC UB-04"},
    {"keywords": ["occupational therapy charge"], "code": "0430", "description": "Occupational Therapy – General", "ref": "NUBC UB-04"},
    {"keywords": ["speech therapy charge"], "code": "0440", "description": "Speech/Language Therapy – General", "ref": "NUBC UB-04"},
    {"keywords": ["ekg revenue"], "code": "0730", "description": "EKG/ECG – General", "ref": "NUBC UB-04"},
    {"keywords": ["ent"], "code": "0470", "description": "Audiology – General", "ref": "NUBC UB-04"},
    {"keywords": ["medical supplies"], "code": "0270", "description": "Medical/Surgical Supplies – General", "ref": "NUBC UB-04"},
    {"keywords": ["dialysis revenue"], "code": "0800", "description": "Inpatient Renal Dialysis – General", "ref": "NUBC UB-04"},
    {"keywords": ["hospice room"], "code": "0651", "description": "Hospice Service – Routine Home Care", "ref": "NUBC UB-04"},
    {"keywords": ["skilled nursing charge", "snf charge"], "code": "0190", "description": "Sub-acute care (level 1)", "ref": "NUBC UB-04"},
]

# --------------------------------------------------------------------------
# Condition / Occurrence / Value codes (UB-04)
# --------------------------------------------------------------------------
CONDITION_CODES: List[dict] = [
    {"keywords": ["military service", "veteran"], "code": "02", "description": "Condition is employment related", "ref": "NUBC Condition Codes"},
    {"keywords": ["auto accident", "motor vehicle"], "code": "04", "description": "HMO enrollee", "ref": "NUBC Condition Codes"},
    {"keywords": ["abortion", "elective termination"], "code": "20", "description": "Beneficiary would not provide information", "ref": "NUBC Condition Codes"},
    {"keywords": ["skilled nursing facility", "snf"], "code": "41", "description": "Partial hospitalization", "ref": "NUBC Condition Codes"},
    {"keywords": ["nonelective"], "code": "A9", "description": "Medical/nonelective admission", "ref": "NUBC Condition Codes"},
    {"keywords": ["religious non-medical"], "code": "44", "description": "Patient being treated at non-acute level", "ref": "NUBC Condition Codes"},
    {"keywords": ["covid-19 related"], "code": "DR", "description": "Disaster Related (COVID-19)", "ref": "NUBC / CMS COVID Guidance"},
]

OCCURRENCE_CODES: List[dict] = [
    {"keywords": ["accident", "injury date"], "code": "01", "description": "Accident/Medical Coverage – date of accident", "ref": "NUBC Occurrence"},
    {"keywords": ["auto accident occ"], "code": "02", "description": "No-fault insurance involved – date of accident", "ref": "NUBC Occurrence"},
    {"keywords": ["accident employment"], "code": "04", "description": "Accident/Employment related – date of accident", "ref": "NUBC Occurrence"},
    {"keywords": ["onset of symptoms"], "code": "11", "description": "Onset of Symptoms/Illness", "ref": "NUBC Occurrence"},
    {"keywords": ["last menstrual"], "code": "10", "description": "Last menstrual period – date", "ref": "NUBC Occurrence"},
    {"keywords": ["start of therapy"], "code": "35", "description": "Date treatment started for physical therapy", "ref": "NUBC Occurrence"},
    {"keywords": ["hospice start"], "code": "42", "description": "Date of Discharge / Hospice election", "ref": "NUBC Occurrence"},
    {"keywords": ["cancer treatment start"], "code": "46", "description": "Date Treatment Started for Radiotherapy", "ref": "NUBC Occurrence"},
]

VALUE_CODES: List[dict] = [
    {"keywords": ["medicare blood deductible"], "code": "06", "description": "Medicare Blood Deductible", "ref": "NUBC Value"},
    {"keywords": ["working aged"], "code": "12", "description": "Working Aged Beneficiary/Spouse with EGHP", "ref": "NUBC Value"},
    {"keywords": ["esrd beneficiary"], "code": "13", "description": "ESRD Beneficiary in 30-month coordination period", "ref": "NUBC Value"},
    {"keywords": ["copayment"], "code": "A1", "description": "Deductible – Payer A", "ref": "NUBC Value"},
    {"keywords": ["coinsurance"], "code": "A2", "description": "Coinsurance – Payer A", "ref": "NUBC Value"},
    {"keywords": ["psychiatric co-pay"], "code": "A3", "description": "Estimated responsibility – Payer A", "ref": "NUBC Value"},
    {"keywords": ["ventilator hours"], "code": "68", "description": "EPO – Patient hours on mechanical ventilation", "ref": "NUBC Value"},
    {"keywords": ["snf days"], "code": "80", "description": "Covered days", "ref": "NUBC Value"},
]

# --------------------------------------------------------------------------
# MS-DRG map (principal diagnosis keywords → DRG) — ~35 entries
# --------------------------------------------------------------------------
MS_DRG_MAP: List[dict] = [
    {"dx_keywords": ["pneumonia"], "code": "193", "description": "Simple Pneumonia & Pleurisy with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["aspiration pneumonia"], "code": "177", "description": "Respiratory Infections & Inflammations with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["heart failure", "chf"], "code": "291", "description": "Heart Failure & Shock with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["stroke", "cerebral infarction"], "code": "064", "description": "Intracranial Hemorrhage or Cerebral Infarction with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["tia", "transient ischemic"], "code": "069", "description": "Transient Ischemia", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["myocardial infarction", "stemi", "nstemi"], "code": "280", "description": "Acute MI, Discharged Alive with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["unstable angina"], "code": "311", "description": "Angina Pectoris", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["atrial fibrillation"], "code": "309", "description": "Cardiac Arrhythmia & Conduction Disorders with CC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["sepsis"], "code": "871", "description": "Septicemia or Severe Sepsis w/o MV >96 hrs with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["septic shock"], "code": "870", "description": "Septicemia or Severe Sepsis with MV >96 hrs", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["copd"], "code": "190", "description": "COPD with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["asthma exacerbation"], "code": "202", "description": "Bronchitis & Asthma with CC/MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["respiratory failure"], "code": "189", "description": "Pulmonary Edema & Respiratory Failure", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["uti", "urinary tract infection"], "code": "689", "description": "Kidney & Urinary Tract Infections with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["pyelonephritis"], "code": "689", "description": "Kidney & Urinary Tract Infections with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["hip fracture", "femur fracture"], "code": "535", "description": "Fractures of Hip & Pelvis with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["hip replacement", "knee replacement"], "code": "470", "description": "Major Joint Replacement or Reattachment of Lower Extremity w/o MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["cabg", "coronary artery bypass"], "code": "236", "description": "Coronary Bypass w/o Cardiac Cath w/o MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["pci", "angioplasty"], "code": "247", "description": "Perc Cardiovascular Proc w/Drug-Eluting Stent w/o MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["acute kidney", "aki"], "code": "682", "description": "Renal Failure with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["gi bleed", "gastrointestinal hemorrhage"], "code": "377", "description": "GI Hemorrhage with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["diverticulitis"], "code": "391", "description": "Esophagitis, Gastroent & Misc Digestive Disorders with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["cholecystitis", "gallstones"], "code": "418", "description": "Laparoscopic Cholecystectomy w/o CDE w/o CC/MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["pancreatitis"], "code": "438", "description": "Disorders of Pancreas Except Malignancy with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["diabetic ketoacidosis", "dka"], "code": "637", "description": "Diabetes with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["cesarean"], "code": "788", "description": "Cesarean Section w/o CC/MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["vaginal delivery"], "code": "807", "description": "Vaginal Delivery w/o Sterilization/D&C w/o CC/MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["depression", "bipolar", "psychiatric"], "code": "885", "description": "Psychoses", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["alcohol dependence", "opioid dependence"], "code": "894", "description": "Alcohol/Drug Abuse or Dependence, Left Against Medical Advice", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["cellulitis", "abscess"], "code": "603", "description": "Cellulitis w/o MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["trauma", "tbi", "multiple injuries"], "code": "963", "description": "Other Multiple Significant Trauma with MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
    {"dx_keywords": ["cancer", "neoplasm"], "code": "846", "description": "Chemotherapy w/o Acute Leukemia as Secondary Diagnosis w/o MCC", "ref": "CMS IPPS FY2024 MS-DRG v41"},
]
