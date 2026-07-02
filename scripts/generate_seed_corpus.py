#!/usr/bin/env python3
"""Generate a synthetic, de-identified healthcare knowledge corpus.

Standard library only (no third-party imports). Usage:

    python3 scripts/generate_seed_corpus.py

Running this script writes one Markdown file per article into
`seed_corpus/` at the repository root, named `<specialty>-<slug>.md`
where `<slug>` is derived from the article title. The script is fully
deterministic: there are no timestamps, no randomness, and no
environment-dependent values, and the fixed ARTICLES list below is
always iterated in the same order. Re-running the script overwrites
the same files with byte-identical content every time.

All article content is original, general medical/educational writing
produced for a retrieval-augmented-generation demo. It intentionally
contains no real or fabricated patient identifiers (no names, MRNs,
SSNs, dates of birth, addresses, or phone numbers) and must not be
used for clinical decision-making.
"""

import os
import re

DISCLAIMER = (
    "*Synthetic educational content — not real patient data. "
    "Do not use for clinical decisions.*"
)

# Each entry is one article: `specialty` (one of the eight fixed
# specialty slugs), `title` (rendered as the H1 and used to derive the
# filename slug), and `body` (2-5 plain paragraphs of general clinical
# knowledge, separated by blank lines, ~150-400 words). The list order
# is fixed on purpose so output is stable across runs.
ARTICLES = [
    # ------------------------------------------------------------------
    # Cardiology
    # ------------------------------------------------------------------
    {
        "specialty": "cardiology",
        "title": "Hypertension: Diagnosis and Long-Term Management",
        "body": """Hypertension is defined by current guidelines as a sustained systolic blood pressure of 130 mmHg or higher, or a diastolic pressure of 80 mmHg or higher, confirmed on repeated office measurements or with out-of-office monitoring such as home blood pressure cuffs or 24-hour ambulatory recordings. Most cases are labeled primary (essential) hypertension, meaning no single identifiable cause is found, though secondary causes such as renal artery stenosis, primary aldosteronism, and obstructive sleep apnea should be considered in resistant or early-onset disease. Chronic elevation in arterial pressure increases the workload on the left ventricle and damages the endothelium of small and large vessels, raising long-term risk for stroke, myocardial infarction, heart failure, and chronic kidney disease.

Initial management emphasizes lifestyle modification: sodium restriction, weight reduction, regular aerobic activity, moderation of alcohol intake, and adoption of a DASH-style diet rich in fruits, vegetables, and low-fat dairy. When pharmacologic therapy is indicated, first-line agents include thiazide-type diuretics, calcium channel blockers such as amlodipine, and renin-angiotensin system blockers such as lisinopril or losartan. Many patients require two or more agents in combination to reach target blood pressure. ACE inhibitors and angiotensin receptor blockers are particularly favored in patients with diabetes or proteinuric kidney disease because of their renoprotective effects, but they require monitoring of serum creatinine and potassium after initiation.

Routine follow-up includes periodic blood pressure checks, assessment for medication side effects such as cough with ACE inhibitors or peripheral edema with dihydropyridine calcium channel blockers, and screening for target-organ damage through fundoscopic examination, urinalysis for proteinuria, and electrocardiography to assess for left ventricular hypertrophy.""",
    },
    {
        "specialty": "cardiology",
        "title": "Heart Failure with Reduced Ejection Fraction",
        "body": """Heart failure with reduced ejection fraction (HFrEF) is defined by a left ventricular ejection fraction of 40% or less, typically measured by transthoracic echocardiography, together with symptoms such as dyspnea, orthopnea, fatigue, and lower extremity edema resulting from impaired systolic pumping function. Common etiologies include ischemic heart disease following myocardial infarction, long-standing hypertension, dilated cardiomyopathy, and valvular disease. Elevated natriuretic peptide levels, particularly BNP or NT-proBNP, support the diagnosis and help distinguish cardiac from non-cardiac causes of breathlessness.

Guideline-directed medical therapy for HFrEF now rests on four pillars: beta-blockers such as carvedilol or metoprolol succinate, angiotensin receptor-neprilysin inhibitors such as sacubitril-valsartan (or an ACE inhibitor when the combination is unavailable), mineralocorticoid receptor antagonists such as spironolactone, and SGLT2 inhibitors such as dapagliflozin, which have demonstrated mortality and hospitalization benefits independent of diabetes status. Loop diuretics like furosemide are used for symptomatic volume management but do not alter long-term prognosis. Device therapy, including implantable cardioverter-defibrillators and cardiac resynchronization therapy, is considered in select patients with persistently reduced ejection fraction despite optimized medical therapy.

Patients are counseled on daily weight monitoring, sodium and fluid restriction, and prompt reporting of weight gain or worsening dyspnea, since decompensated heart failure is a leading cause of hospital readmission. Regular follow-up echocardiography helps track ventricular remodeling and guides titration of therapy.""",
    },
    {
        "specialty": "cardiology",
        "title": "Atrial Fibrillation: Rate Control, Rhythm Control, and Stroke Prevention",
        "body": """Atrial fibrillation is the most common sustained cardiac arrhythmia, characterized by disorganized atrial electrical activity that produces an irregularly irregular ventricular rhythm on electrocardiogram and loss of coordinated atrial contraction. It may be paroxysmal, persistent, or permanent, and risk factors include advancing age, hypertension, obesity, obstructive sleep apnea, hyperthyroidism, and structural heart disease. Because stagnant blood in the fibrillating left atrial appendage predisposes to thrombus formation, atrial fibrillation substantially raises the risk of embolic stroke.

Management follows two parallel goals: controlling ventricular rate or restoring sinus rhythm, and preventing thromboembolism. Rate control is typically achieved with beta-blockers or non-dihydropyridine calcium channel blockers such as diltiazem, while rhythm control may involve antiarrhythmic drugs, electrical cardioversion, or catheter ablation, particularly in younger or symptomatic patients. The choice between strategies is individualized, as trials have generally shown similar mortality outcomes between rate and rhythm control approaches.

Stroke risk is stratified using the CHA2DS2-VASc score, which incorporates congestive heart failure, hypertension, age, diabetes, prior stroke, vascular disease, and sex category. Patients with a sufficiently elevated score are anticoagulated, most often with a direct oral anticoagulant such as apixaban or rivaroxaban, which has largely supplanted warfarin outside of mechanical valve or significant mitral stenosis cases due to more predictable dosing and lower intracranial hemorrhage risk. Bleeding risk is weighed using tools such as the HAS-BLED score before committing a patient to long-term anticoagulation.""",
    },
    {
        "specialty": "cardiology",
        "title": "ST-Elevation Myocardial Infarction: Recognition and Reperfusion",
        "body": """ST-elevation myocardial infarction (STEMI) results from abrupt, complete occlusion of a coronary artery, most commonly due to rupture of an atherosclerotic plaque with superimposed thrombus formation, leading to transmural myocardial ischemia and necrosis if flow is not promptly restored. Patients classically present with substernal chest pressure radiating to the arm or jaw, diaphoresis, and dyspnea, although presentations in women, older adults, and patients with diabetes are frequently atypical. The diagnostic hallmark is ST-segment elevation in two or more contiguous electrocardiographic leads, accompanied by a rise in cardiac biomarkers such as high-sensitivity troponin.

Time to reperfusion is the dominant determinant of outcome, encapsulated in the phrase "time is muscle." Primary percutaneous coronary intervention (PCI), in which an interventional cardiologist opens the occluded vessel with balloon angioplasty and typically places a drug-eluting stent, is the preferred reperfusion strategy when it can be performed within the guideline-recommended window at a capable facility. When timely PCI is not available, fibrinolytic therapy with agents such as tenecteplase may be administered, followed by transfer for angiography.

Adjunctive medical therapy includes dual antiplatelet therapy with aspirin and a P2Y12 inhibitor such as ticagrelor, anticoagulation, high-intensity statin therapy, and beta-blockade once the patient is hemodynamically stable. After the acute event, cardiac rehabilitation and secondary prevention measures, including risk factor modification and adherence to guideline-directed medical therapy, reduce the risk of recurrent events and improve long-term survival.""",
    },
    {
        "specialty": "cardiology",
        "title": "Aortic Stenosis and the Role of Echocardiography",
        "body": """Aortic stenosis is the narrowing of the aortic valve orifice, most often caused in older adults by progressive calcific degeneration of a trileaflet valve, or in younger patients by a congenitally bicuspid valve that calcifies earlier in life. As the valve area shrinks, the left ventricle must generate higher pressures to maintain forward flow, resulting in compensatory concentric hypertrophy. The classic symptom triad of severe aortic stenosis is exertional angina, syncope, and dyspnea, and the onset of symptoms marks a critical inflection point after which survival declines sharply without intervention.

Transthoracic echocardiography is the primary diagnostic tool, providing the aortic valve area, mean transvalvular gradient, and peak jet velocity, along with assessment of left ventricular size, wall thickness, and ejection fraction. A physical examination finding of a harsh crescendo-decrescendo systolic murmur radiating to the carotids should prompt echocardiographic evaluation. Cardiac catheterization or CT angiography may be used to further characterize valve anatomy or coexisting coronary artery disease prior to intervention.

Once severe aortic stenosis becomes symptomatic, valve replacement is indicated, as medical therapy does not alter the natural history of the disease. Transcatheter aortic valve replacement (TAVR) has become an option across the surgical risk spectrum, delivering a bioprosthetic valve via catheter, typically through the femoral artery, while surgical aortic valve replacement remains preferred in certain younger or lower-risk patients, particularly those with concomitant conditions requiring open surgery.""",
    },
    {
        "specialty": "cardiology",
        "title": "Dyslipidemia and Statin Therapy for Cardiovascular Risk Reduction",
        "body": """Dyslipidemia refers to abnormal concentrations of circulating lipoproteins, most importantly elevated low-density lipoprotein cholesterol (LDL-C), which promotes atherosclerotic plaque formation within arterial walls and is a major modifiable risk factor for coronary artery disease, ischemic stroke, and peripheral arterial disease. A fasting or non-fasting lipid panel measuring total cholesterol, LDL-C, HDL-C, and triglycerides remains the primary screening tool, often supplemented by calculation of a ten-year atherosclerotic cardiovascular disease risk score that incorporates age, blood pressure, smoking status, and diabetes.

Statins, such as atorvastatin and rosuvastatin, are the cornerstone of pharmacologic therapy, working by inhibiting HMG-CoA reductase, the rate-limiting enzyme in hepatic cholesterol synthesis, which upregulates LDL receptor expression and increases clearance of circulating LDL particles from the blood. High-intensity statin therapy is recommended for patients with established atherosclerotic cardiovascular disease and for many patients with diabetes or markedly elevated LDL-C. For patients who do not reach goal on maximally tolerated statin therapy, adjunctive agents such as ezetimibe, which blocks intestinal cholesterol absorption, or PCSK9 inhibitors, which enhance LDL receptor recycling, may be added.

Statin therapy is generally well tolerated, though it can cause myalgias and, rarely, clinically significant myopathy or transaminitis, so baseline and follow-up liver function testing and symptom monitoring are common practice. Lifestyle measures, including dietary saturated fat reduction, weight management, and exercise, remain foundational alongside pharmacotherapy for comprehensive cardiovascular risk reduction.""",
    },
    # ------------------------------------------------------------------
    # Endocrinology
    # ------------------------------------------------------------------
    {
        "specialty": "endocrinology",
        "title": "Type 2 Diabetes Mellitus: Pathophysiology and First-Line Therapy",
        "body": """Type 2 diabetes mellitus arises from a combination of peripheral insulin resistance and progressive pancreatic beta-cell dysfunction, resulting in chronic hyperglycemia. Unlike type 1 diabetes, most patients retain some endogenous insulin production, particularly early in the disease course, and the condition is strongly associated with obesity, sedentary lifestyle, and genetic predisposition. Diagnosis is established by a fasting plasma glucose of 126 mg/dL or higher, a hemoglobin A1c of 6.5% or higher, or an abnormal oral glucose tolerance test, with confirmation on repeat testing in asymptomatic individuals.

Metformin remains the preferred first-line pharmacologic agent for most patients, acting primarily by reducing hepatic gluconeogenesis and improving peripheral insulin sensitivity, with the added benefits of weight neutrality and a low risk of hypoglycemia when used as monotherapy. For patients with established cardiovascular disease, heart failure, or chronic kidney disease, guidelines increasingly favor early addition of a GLP-1 receptor agonist such as semaglutide or an SGLT2 inhibitor such as empagliflozin, both of which have demonstrated cardiovascular and renal protective effects beyond glucose lowering. Sulfonylureas and insulin remain options when additional glycemic control is needed.

Comprehensive management extends beyond glucose control to include blood pressure and lipid management, annual dilated eye examinations to screen for retinopathy, foot examinations to detect early neuropathy, and urine albumin-to-creatinine ratio testing to monitor for diabetic nephropathy, reflecting the multisystem nature of chronic hyperglycemic damage.""",
    },
    {
        "specialty": "endocrinology",
        "title": "Type 1 Diabetes and Insulin Replacement Therapy",
        "body": """Type 1 diabetes mellitus results from autoimmune destruction of insulin-producing pancreatic beta cells, leading to an absolute deficiency of endogenous insulin. It most often presents in childhood or adolescence but can develop at any age, sometimes as latent autoimmune diabetes in adults. Presenting symptoms frequently include polyuria, polydipsia, unintended weight loss, and, in more severe cases, diabetic ketoacidosis, a life-threatening state of hyperglycemia, ketosis, and metabolic acidosis that requires urgent treatment with intravenous fluids, insulin infusion, and electrolyte correction, particularly close monitoring of potassium.

Lifelong exogenous insulin replacement is required for survival. Most patients use a basal-bolus regimen combining a long-acting basal insulin, such as insulin glargine, to suppress hepatic glucose output between meals, with rapid-acting insulin analogs, such as insulin lispro or insulin aspart, administered before meals to cover carbohydrate intake. Many patients now use continuous subcutaneous insulin infusion pumps paired with continuous glucose monitors, and hybrid closed-loop systems can automatically adjust basal delivery based on real-time glucose trends.

Ongoing management requires patient education in carbohydrate counting, insulin dose adjustment, and recognition of hypoglycemia symptoms such as tremor, diaphoresis, and confusion. Long-term surveillance mirrors that of type 2 diabetes, including regular hemoglobin A1c measurement, retinal examinations, and screening for microvascular and macrovascular complications, since durable glycemic control substantially reduces the risk of nephropathy, neuropathy, and retinopathy.""",
    },
    {
        "specialty": "endocrinology",
        "title": "Hypothyroidism and Levothyroxine Replacement",
        "body": """Hypothyroidism is a state of insufficient thyroid hormone production, most commonly caused in iodine-sufficient regions by Hashimoto's thyroiditis, an autoimmune process in which antithyroid peroxidase antibodies gradually destroy thyroid follicular tissue. Other causes include prior thyroidectomy, radioactive iodine ablation, and certain medications such as lithium and amiodarone. Clinical features develop gradually and include fatigue, cold intolerance, weight gain, constipation, dry skin, and menstrual irregularities, reflecting the widespread metabolic role of thyroid hormone.

The diagnosis is confirmed biochemically: primary hypothyroidism shows an elevated thyroid-stimulating hormone (TSH) with a low free thyroxine (T4), while subclinical hypothyroidism shows an elevated TSH with normal free T4. Central hypothyroidism, arising from pituitary or hypothalamic disease, is uncommon and presents with a low or inappropriately normal TSH alongside low free T4.

Treatment consists of daily oral levothyroxine, a synthetic form of T4, dosed to restore TSH to the normal reference range, typically taken on an empty stomach to optimize absorption and separated from calcium, iron supplements, and certain other medications that impair intestinal uptake. Dose requirements are influenced by body weight, age, pregnancy, and concurrent malabsorptive conditions, and are typically reassessed with repeat TSH testing roughly six to eight weeks after any dose change. Untreated severe hypothyroidism can rarely progress to myxedema coma, a medical emergency marked by hypothermia, altered mental status, and hemodynamic instability.""",
    },
    {
        "specialty": "endocrinology",
        "title": "Graves' Disease and Management of Hyperthyroidism",
        "body": """Graves' disease is the most common cause of hyperthyroidism in iodine-sufficient populations, driven by circulating thyroid-stimulating immunoglobulins that bind and activate the TSH receptor, causing diffuse thyroid gland enlargement and excess hormone secretion. Distinctive clinical features can include a diffuse goiter, Graves' ophthalmopathy with proptosis and periorbital edema, and pretibial myxedema, though many patients present simply with the systemic effects of thyrotoxicosis: palpitations, heat intolerance, tremor, anxiety, weight loss despite increased appetite, and, on examination, tachycardia or atrial fibrillation.

Diagnosis is supported by a suppressed TSH with elevated free T4 and/or free T3, along with positive thyrotropin receptor antibodies. A radioactive iodine uptake scan can help distinguish Graves' disease, which shows diffusely increased uptake, from other causes of thyrotoxicosis such as subacute thyroiditis, which characteristically shows low uptake.

Initial symptom control often involves a beta-blocker such as propranolol to blunt adrenergic symptoms. Definitive management options include antithyroid medications such as methimazole, which inhibits thyroid hormone synthesis, radioactive iodine ablation, which destroys thyroid tissue over several weeks, and surgical thyroidectomy. The choice among these depends on goiter size, ophthalmopathy severity, pregnancy status, and patient preference. Methimazole carries a rare but serious risk of agranulocytosis and hepatotoxicity, so patients are counseled to seek urgent evaluation for fever, sore throat, or jaundice while on therapy.""",
    },
    {
        "specialty": "endocrinology",
        "title": "Osteoporosis Screening and Bisphosphonate Therapy",
        "body": """Osteoporosis is a skeletal disorder characterized by low bone mineral density and microarchitectural deterioration of bone tissue, resulting in increased bone fragility and susceptibility to fracture, particularly of the hip, vertebrae, and distal radius. It is more common in postmenopausal women due to the accelerated bone loss that follows estrogen decline, but also occurs in men and can be secondary to glucocorticoid use, hyperthyroidism, hyperparathyroidism, or prolonged immobilization.

Screening is performed using dual-energy X-ray absorptiometry (DEXA), which reports bone mineral density as a T-score comparing the patient to a young healthy reference population; a T-score of -2.5 or lower at the hip or spine establishes the diagnosis, while a T-score between -1.0 and -2.5 defines osteopenia. The FRAX tool combines bone density with clinical risk factors, such as age, prior fracture, and glucocorticoid use, to estimate ten-year fracture risk and guide treatment decisions.

First-line pharmacologic therapy typically involves oral bisphosphonates, such as alendronate or risedronate, which bind hydroxyapatite in bone and inhibit osteoclast-mediated resorption, thereby increasing bone density and reducing fracture risk. Patients are instructed to take these medications on an empty stomach with a full glass of water and remain upright for at least thirty minutes to reduce esophageal irritation. For patients with very high fracture risk or intolerance to bisphosphonates, alternatives include denosumab, a monoclonal antibody against RANKL, and anabolic agents such as teriparatide. Adequate calcium and vitamin D intake and weight-bearing exercise are recommended as adjuncts to any pharmacologic regimen.""",
    },
    {
        "specialty": "endocrinology",
        "title": "Primary Adrenal Insufficiency (Addison's Disease)",
        "body": """Primary adrenal insufficiency occurs when the adrenal cortex is damaged or destroyed and can no longer produce adequate cortisol and, often, aldosterone. In resource-rich settings, autoimmune adrenalitis is the leading cause, while infectious causes such as tuberculosis remain important globally. Because cortisol normally suppresses corticotropin-releasing hormone and adrenocorticotropic hormone (ACTH) through negative feedback, primary disease is accompanied by markedly elevated ACTH, which can cause the hyperpigmentation of skin and mucous membranes classically associated with Addison's disease.

Clinical features are often insidious and nonspecific, including fatigue, weight loss, anorexia, nausea, and orthostatic hypotension, which can make early diagnosis challenging. Salt craving and hyperkalemia may occur when aldosterone deficiency coexists, reflecting impaired renal sodium retention and potassium excretion. An acute adrenal crisis, precipitated by physiologic stress such as infection or surgery in an undiagnosed or under-treated patient, presents with severe hypotension, shock, vomiting, and abdominal pain, and constitutes a medical emergency.

Diagnosis relies on a morning serum cortisol level and, when equivocal, a cosyntropin (ACTH) stimulation test showing an inadequate cortisol rise. Treatment requires lifelong glucocorticoid replacement, typically with hydrocortisone dosed to mimic the body's natural diurnal rhythm, plus fludrocortisone to replace mineralocorticoid activity when aldosterone is deficient. Patients are educated to increase glucocorticoid dosing during illness or surgical stress ("stress dosing") and to carry emergency injectable hydrocortisone, since failure to do so can precipitate a life-threatening adrenal crisis.""",
    },
    # ------------------------------------------------------------------
    # Radiology
    # ------------------------------------------------------------------
    {
        "specialty": "radiology",
        "title": "Chest Radiography: Fundamentals of Interpretation",
        "body": """The chest radiograph remains one of the most frequently ordered imaging studies, valued for its low cost, wide availability, and low radiation dose relative to cross-sectional imaging. A standard posteroanterior and lateral chest X-ray series allows assessment of the lungs, cardiac silhouette, mediastinum, pleura, and bony thorax. A systematic reading approach, evaluating technical adequacy and then working through airway, bones, cardiac silhouette, diaphragm, effusions or edges (pleura), and fields (lungs) in a structured fashion, helps avoid missed findings.

Common abnormalities include consolidation, which appears as an area of increased opacity that obscures adjacent vessels and may represent pneumonia; pleural effusion, which blunts the costophrenic angle and layers dependently; pneumothorax, identified by a visceral pleural line with absent lung markings peripheral to it; and cardiomegaly, suggested by a cardiothoracic ratio exceeding 0.5 on a properly positioned PA film. Interstitial patterns, such as reticular or nodular opacities, may point toward pulmonary fibrosis or other interstitial lung disease and often warrant further characterization with high-resolution CT.

Portable anteroposterior films, frequently obtained in critically ill or immobile patients, have technical limitations including cardiac magnification and reduced detail compared with standard upright PA films, which should be considered when interpreting findings such as apparent cardiomegaly. Comparison with prior imaging is essential whenever available, since a stable finding over time is far less concerning than a new or rapidly evolving one.""",
    },
    {
        "specialty": "radiology",
        "title": "Principles of Computed Tomography and Contrast Use",
        "body": """Computed tomography (CT) generates cross-sectional images by rotating an X-ray source and detector array around the patient and mathematically reconstructing attenuation data into axial, coronal, and sagittal images. Compared with conventional radiography, CT offers superior contrast resolution and eliminates the superimposition of overlying structures, making it invaluable for evaluating trauma, acute abdominal pain, pulmonary nodules, and staging of malignancy. Its principal drawback is a substantially higher radiation dose than plain radiography, which has driven adoption of dose-reduction protocols and "as low as reasonably achievable" (ALARA) principles, particularly in children and patients requiring serial imaging.

Iodinated intravenous contrast is frequently administered to enhance vascular structures and highlight the differential enhancement patterns of organs and lesions; timing of image acquisition relative to contrast injection, such as arterial versus portal venous phase, is chosen based on the clinical question. Contrast administration requires screening for risk factors including significant renal impairment, given the association between iodinated contrast and contrast-induced nephropathy, and prior contrast reactions, which may warrant premedication or use of an alternative imaging modality.

CT angiography has become a first-line tool for evaluating suspected pulmonary embolism, aortic dissection, and cerebrovascular disease, offering rapid acquisition and high spatial resolution. Radiologists must balance diagnostic yield against cumulative radiation exposure and contrast-related risk when recommending CT versus alternative modalities such as ultrasound or MRI.""",
    },
    {
        "specialty": "radiology",
        "title": "Magnetic Resonance Imaging: Physics and Clinical Applications",
        "body": """Magnetic resonance imaging (MRI) uses a strong static magnetic field, radiofrequency pulses, and magnetic field gradients to align and perturb hydrogen protons within body tissue, generating detailed images based on differences in proton density and relaxation properties, without ionizing radiation. T1-weighted sequences are useful for demonstrating anatomy, with fat appearing bright and fluid appearing dark, while T2-weighted sequences highlight fluid and edema as bright signal, making them sensitive to inflammation, infarction, and many tumors. Additional sequences, such as diffusion-weighted imaging, are particularly valuable for detecting acute ischemic stroke within minutes of symptom onset.

MRI's excellent soft-tissue contrast makes it the modality of choice for evaluating the brain and spinal cord, joints and ligaments, and many soft-tissue and hepatic lesions. Gadolinium-based contrast agents are often administered to improve lesion conspicuity and characterize enhancement patterns, though they must be used cautiously in patients with severely reduced kidney function because of a rare but serious association with nephrogenic systemic fibrosis.

Because the technique relies on a powerful magnet, absolute contraindications include certain implanted ferromagnetic devices, and all patients and staff must be screened for pacemakers, aneurysm clips, cochlear implants, and metallic foreign bodies before entering the scanner room. Examinations typically take longer than CT and require patients to remain still, which can be challenging for claustrophobic or critically ill patients, occasionally necessitating sedation.""",
    },
    {
        "specialty": "radiology",
        "title": "Mammography and the BI-RADS Reporting System",
        "body": """Mammography uses low-dose X-ray imaging to detect breast abnormalities, including masses, architectural distortion, and microcalcifications, often before they are palpable on clinical examination. Screening mammography is recommended at regular intervals for average-risk women beginning in their forties, with the exact starting age and frequency varying somewhat between guideline bodies, while women at elevated hereditary risk, such as BRCA1 or BRCA2 mutation carriers, may begin screening earlier and supplement mammography with breast MRI.

Findings are standardized using the Breast Imaging-Reporting and Data System (BI-RADS), a categorical scale ranging from BI-RADS 0, indicating incomplete assessment requiring additional imaging, through BI-RADS 1 and 2 for normal or benign findings, BI-RADS 3 for probably benign findings warranting short-interval follow-up, BI-RADS 4 for suspicious findings warranting biopsy, to BI-RADS 5 for findings highly suggestive of malignancy. This standardized language improves communication between radiologists and referring clinicians and supports consistent management decisions.

When a suspicious finding is identified, diagnostic mammography with additional views, targeted ultrasound, and image-guided core needle biopsy are used to further characterize the lesion and obtain tissue diagnosis. Digital breast tomosynthesis, which acquires multiple low-dose projections to reconstruct a pseudo-three-dimensional image of the breast, has improved cancer detection rates and reduced false-positive recalls compared with conventional two-dimensional mammography alone, particularly in women with dense breast tissue.""",
    },
    {
        "specialty": "radiology",
        "title": "Diagnostic Ultrasound: Principles and Common Uses",
        "body": """Diagnostic ultrasound uses high-frequency sound waves emitted from a transducer to generate real-time images based on the reflection of echoes at tissue interfaces of differing acoustic impedance. Because it avoids ionizing radiation and equipment is portable and relatively inexpensive, ultrasound is widely used for obstetric imaging, abdominal and pelvic evaluation, vascular assessment, and point-of-care applications at the bedside, including the rapid trauma assessment known as the FAST examination.

Doppler ultrasound adds the ability to assess blood flow direction and velocity, making it central to evaluating suspected deep vein thrombosis, carotid artery stenosis, and abnormalities of arterial and venous flow throughout the body. Echocardiography, a specialized application of ultrasound, evaluates cardiac chamber size, wall motion, valvular function, and ejection fraction, and is often the first-line imaging study for suspected structural heart disease or heart failure.

Ultrasound image quality is operator-dependent and can be limited by patient body habitus, overlying bowel gas, and the acoustic shadowing produced by bone or calcification, which distinguishes it from cross-sectional modalities like CT and MRI that are less affected by these factors. Despite these limitations, its lack of radiation makes ultrasound the preferred first-line modality in pregnant patients and children whenever it can adequately answer the clinical question, and it plays a central role in image-guided procedures such as biopsies and line placement.""",
    },
    {
        "specialty": "radiology",
        "title": "PET/CT Imaging in Oncologic Staging",
        "body": """Positron emission tomography combined with computed tomography (PET/CT) integrates functional metabolic imaging with detailed anatomic localization in a single study. The most widely used radiotracer, fluorodeoxyglucose labeled with fluorine-18 (FDG), is a glucose analog that accumulates preferentially in tissues with high metabolic activity, including many malignant tumors, allowing detection of primary tumors, regional lymph node involvement, and distant metastatic disease based on abnormal tracer uptake rather than size alone.

FDG-PET/CT is widely used in the staging and restaging of lymphoma, lung cancer, and several other malignancies, in assessing response to chemotherapy or radiation, and in distinguishing viable residual tumor from post-treatment scar tissue, which can appear indeterminate on anatomic imaging alone. Quantitative uptake is often reported using the standardized uptake value (SUV), which allows comparison across time points in the same patient, though it can be affected by technical factors such as blood glucose level and imaging timing after tracer injection.

Because glucose-avid inflammatory and infectious processes can also demonstrate increased FDG uptake, PET/CT findings must always be interpreted alongside clinical history, prior imaging, and, when necessary, tissue biopsy to avoid false-positive interpretation of malignancy. Patients are typically asked to fast for several hours before the study to reduce background myocardial and skeletal muscle uptake and to optimize image quality, and blood glucose is generally checked before tracer injection since hyperglycemia can reduce tumor conspicuity.""",
    },
    # ------------------------------------------------------------------
    # Infectious Disease
    # ------------------------------------------------------------------
    {
        "specialty": "infectious_disease",
        "title": "Community-Acquired Pneumonia: Diagnosis and Antibiotic Selection",
        "body": """Community-acquired pneumonia (CAP) is an acute lower respiratory tract infection acquired outside the hospital setting, typically presenting with fever, productive cough, pleuritic chest pain, and dyspnea, along with a new infiltrate on chest radiography. Streptococcus pneumoniae remains the most commonly identified bacterial pathogen, though atypical organisms such as Mycoplasma pneumoniae and Legionella pneumophila, along with respiratory viruses, account for a significant proportion of cases, particularly in outpatients.

Severity assessment tools such as the CURB-65 score, which incorporates confusion, blood urea nitrogen, respiratory rate, blood pressure, and age over 65, help guide decisions about outpatient management versus hospital admission. Outpatient treatment for previously healthy adults typically involves a macrolide such as azithromycin or doxycycline, while patients with comorbidities or in regions with significant macrolide resistance often receive a respiratory fluoroquinolone such as levofloxacin or combination therapy with a beta-lactam plus a macrolide. Hospitalized patients, particularly those requiring intensive care, warrant broader empiric coverage and closer monitoring for complications such as parapneumonic effusion or empyema.

Blood cultures, sputum culture, and urinary antigen testing for pneumococcus and Legionella may be obtained in more severe presentations to guide targeted therapy and support antimicrobial stewardship by allowing de-escalation once a pathogen is identified. Vaccination against Streptococcus pneumoniae and influenza remains an important preventive measure, particularly in older adults and those with chronic cardiopulmonary disease.""",
    },
    {
        "specialty": "infectious_disease",
        "title": "Uncomplicated Urinary Tract Infection in Adults",
        "body": """Urinary tract infection (UTI) refers to bacterial infection of the bladder (cystitis) or, when ascending, the kidney (pyelonephritis), and is among the most common bacterial infections encountered in outpatient practice, disproportionately affecting women due to a shorter urethra and its proximity to the perineum. Escherichia coli accounts for the large majority of uncomplicated cases, with other Enterobacteriaceae and Staphylococcus saprophyticus implicated less frequently. Typical symptoms of cystitis include dysuria, urinary frequency, urgency, and suprapubic discomfort, generally without fever, while pyelonephritis additionally presents with fever, flank pain, and costovertebral angle tenderness.

Diagnosis of uncomplicated cystitis in a patient with classic symptoms is often made clinically or supported by urinalysis showing pyuria and bacteriuria, with urine culture reserved for recurrent infections, treatment failure, pregnancy, or suspected pyelonephritis. First-line antibiotic choices for uncomplicated cystitis include nitrofurantoin, trimethoprim-sulfamethoxazole where local resistance rates permit, and fosfomycin, generally given as a short course of three to seven days depending on the agent selected. Pyelonephritis typically requires a longer course, often with a fluoroquinolone or an oral agent following initial intravenous therapy in more severe cases, and may warrant imaging if there is concern for obstruction or abscess.

Recurrent UTIs, complicated infections in men, or infections associated with catheters, structural abnormalities, or pregnancy require individualized evaluation, since treatment failure or progression to bacteremia and sepsis carries substantially higher morbidity in these populations.""",
    },
    {
        "specialty": "infectious_disease",
        "title": "Sepsis Recognition and Early Management",
        "body": """Sepsis is a life-threatening syndrome of organ dysfunction caused by a dysregulated host response to infection, distinguishing it from uncomplicated infection by evidence of physiologic decompensation such as altered mental status, hypotension, tachypnea, or laboratory abnormalities including an elevated lactate. Septic shock, the most severe manifestation, is defined by persistent hypotension requiring vasopressor support to maintain adequate mean arterial pressure despite fluid resuscitation, combined with a serum lactate greater than 2 mmol/L, and carries substantial mortality risk.

Early recognition relies on clinical suspicion combined with screening tools such as the quick Sequential Organ Failure Assessment (qSOFA), which flags patients with altered mentation, respiratory rate of 22 or higher, or systolic blood pressure of 100 mmHg or lower as being at higher risk of poor outcomes from infection. Once sepsis is suspected, management follows a time-sensitive bundle: obtaining blood cultures before antibiotics when feasible, measuring serum lactate, administering broad-spectrum empiric antibiotics within the first hour, and initiating rapid intravenous crystalloid fluid resuscitation.

Antibiotic selection is guided by the suspected source of infection, local resistance patterns, and patient-specific risk factors for resistant organisms, with de-escalation to narrower-spectrum therapy once culture results and clinical response are known. Source control, such as drainage of an abscess or removal of an infected catheter, is essential whenever an identifiable focus is present, since antibiotics alone are often insufficient to control infection arising from an undrained source.""",
    },
    {
        "specialty": "infectious_disease",
        "title": "Tuberculosis: Latent Infection Versus Active Disease",
        "body": """Tuberculosis (TB) is caused by Mycobacterium tuberculosis, an acid-fast bacillus transmitted through inhalation of airborne droplet nuclei, most often affecting the lungs but capable of involving nearly any organ system. Following initial infection, most immunocompetent individuals contain the organism within granulomas, resulting in latent tuberculosis infection, a state in which the bacteria remain viable but dormant and the person is asymptomatic and non-contagious. A minority of infected individuals, particularly those who are immunosuppressed, progress to active disease either soon after exposure or after years of latency through reactivation.

Active pulmonary TB classically presents with a chronic productive cough, hemoptysis, night sweats, fever, and unintentional weight loss, with classic chest radiographic findings of upper lobe cavitary disease. Diagnosis relies on sputum acid-fast bacillus smear and culture, with culture remaining the gold standard, alongside more rapid nucleic acid amplification testing. Latent infection is identified through the tuberculin skin test or interferon-gamma release assays, neither of which can distinguish latent infection from active disease on their own, making chest imaging and clinical assessment essential in anyone testing positive.

Active disease treatment typically involves a multidrug regimen, most commonly isoniazid, rifampin, pyrazinamide, and ethambutol during an initial intensive phase, to reduce the emergence of drug resistance, followed by a continuation phase of fewer agents. Latent infection is treated with shorter regimens, such as isoniazid with rifapentine, to reduce the lifetime risk of progression to active, transmissible disease.""",
    },
    {
        "specialty": "infectious_disease",
        "title": "HIV Infection: Antiretroviral Therapy and Monitoring",
        "body": """Human immunodeficiency virus (HIV) is a retrovirus that infects and progressively depletes CD4-positive T lymphocytes, impairing cell-mediated immunity and, without treatment, eventually leading to acquired immunodeficiency syndrome (AIDS), a stage defined by a CD4 count below 200 cells per microliter or the occurrence of specific opportunistic infections and malignancies. Transmission occurs through sexual contact, exposure to infected blood, and perinatally from mother to child, and modern screening relies on combination antigen-antibody immunoassays followed by confirmatory testing.

The cornerstone of management is combination antiretroviral therapy (ART), typically consisting of two nucleoside reverse transcriptase inhibitors paired with a third agent from a different drug class, most often an integrase strand transfer inhibitor such as dolutegravir due to its favorable efficacy and tolerability profile. Current guidelines recommend initiating ART promptly after diagnosis regardless of CD4 count, since durable viral suppression both preserves immune function and prevents transmission to others, an approach summarized as "treatment as prevention."

Ongoing monitoring includes periodic HIV RNA viral load testing to confirm virologic suppression, CD4 count trends to assess immune recovery, and screening for ART-related metabolic and renal effects. Patients with advanced immunosuppression require prophylaxis against opportunistic infections such as Pneumocystis jirovecii pneumonia. Pre-exposure prophylaxis, using agents such as tenofovir-based regimens, is an important prevention strategy for individuals at ongoing substantial risk of acquiring HIV.""",
    },
    {
        "specialty": "infectious_disease",
        "title": "Clostridioides difficile Infection and Treatment",
        "body": """Clostridioides difficile is a spore-forming, toxin-producing anaerobic bacterium and a leading cause of healthcare-associated diarrhea, typically arising after disruption of normal colonic flora by antibiotic exposure allows the organism to proliferate and elaborate toxins that damage the colonic mucosa. Fluoroquinolones, clindamycin, and broad-spectrum cephalosporins are particularly associated with elevated risk, though any antibiotic exposure can predispose to infection. Additional risk factors include advanced age, hospitalization, and use of proton pump inhibitors.

Clinical presentation ranges from mild watery diarrhea to fulminant colitis with toxic megacolon, and characteristic features include frequent loose stools, abdominal cramping, and low-grade fever. Diagnosis is generally established through stool testing, most often a combination of a sensitive nucleic acid amplification test targeting the toxin gene and a toxin enzyme immunoassay, since a positive molecular test alone can reflect asymptomatic colonization rather than active toxin-mediated disease.

First-line treatment for an initial episode consists of oral vancomycin or fidaxomicin, both of which act locally within the intestinal lumen; metronidazole is now generally reserved for milder cases when preferred agents are unavailable, reflecting evolving evidence and guideline updates. Recurrent infection, which affects a substantial minority of patients after successful initial treatment, may be managed with a prolonged or pulsed vancomycin taper, fidaxomicin, or, for multiple recurrences, fecal microbiota transplantation, which restores a diverse colonic flora and has demonstrated high efficacy in breaking the cycle of relapse. Discontinuing unnecessary antibiotics and practicing contact precautions are key infection control measures.""",
    },
    # ------------------------------------------------------------------
    # Oncology
    # ------------------------------------------------------------------
    {
        "specialty": "oncology",
        "title": "Breast Cancer: Staging and Receptor-Directed Therapy",
        "body": """Breast cancer arises from malignant transformation of ductal or lobular epithelial cells and is the most commonly diagnosed cancer in women worldwide. Diagnostic evaluation typically begins with mammography or ultrasound following detection of a palpable mass or a screening abnormality, with core needle biopsy providing tissue for histologic diagnosis and biomarker testing. Every invasive breast cancer is routinely tested for estrogen receptor (ER), progesterone receptor (PR), and human epidermal growth factor receptor 2 (HER2) status, since these markers guide both prognosis and treatment selection.

Staging incorporates tumor size, regional lymph node involvement often assessed through sentinel lymph node biopsy, and the presence or absence of distant metastasis, following the TNM staging framework. Local therapy typically involves either breast-conserving surgery with adjuvant radiation or mastectomy, depending on tumor characteristics and patient preference. Systemic therapy is tailored to receptor status: hormone receptor-positive tumors are treated with endocrine therapy such as tamoxifen or aromatase inhibitors, HER2-positive tumors receive HER2-targeted monoclonal antibodies such as trastuzumab, and triple-negative tumors, which lack all three receptors, are generally treated with cytotoxic chemotherapy given the absence of a targetable receptor pathway.

Multigene genomic assays can help identify which patients with early-stage, hormone receptor-positive, node-negative disease are likely to benefit from adjuvant chemotherapy versus endocrine therapy alone, refining treatment decisions beyond traditional clinicopathologic factors and helping many lower-risk patients safely avoid chemotherapy exposure.""",
    },
    {
        "specialty": "oncology",
        "title": "Lung Cancer: Histologic Subtypes and Screening",
        "body": """Lung cancer is broadly divided into non-small cell lung cancer (NSCLC), which accounts for roughly eighty-five percent of cases and includes adenocarcinoma and squamous cell carcinoma subtypes, and small cell lung cancer (SCLC), a more aggressive neuroendocrine tumor strongly associated with cigarette smoking and characterized by rapid growth and early metastatic spread. Cigarette smoking remains the dominant risk factor for both types, though adenocarcinoma also occurs in never-smokers, particularly in association with specific driver mutations.

Low-dose CT screening is recommended for adults with a substantial smoking history within defined age ranges, since it has been shown to reduce lung cancer mortality by detecting tumors at earlier, more treatable stages compared with chest radiography. When a suspicious nodule or mass is identified, tissue diagnosis is obtained through bronchoscopy, CT-guided percutaneous biopsy, or surgical sampling, and staging typically involves CT of the chest and abdomen, PET/CT, and, when intrathoracic lymph node involvement is suspected, mediastinal sampling.

For NSCLC, molecular testing for driver alterations such as EGFR mutations, ALK rearrangements, and PD-L1 expression has become standard, enabling use of targeted tyrosine kinase inhibitors or immune checkpoint inhibitors in appropriate patients, in addition to surgery, radiation, and conventional chemotherapy depending on stage. SCLC, in contrast, is usually treated with combination chemotherapy and radiation given its propensity for early micrometastatic spread, even when imaging suggests localized disease at diagnosis.""",
    },
    {
        "specialty": "oncology",
        "title": "Colorectal Cancer Screening and Treatment Overview",
        "body": """Colorectal cancer typically develops through a well-characterized adenoma-to-carcinoma sequence, in which accumulating genetic mutations transform benign colonic polyps into invasive malignancy over years to decades, a timeline that underlies the rationale for screening programs aimed at detecting and removing precancerous polyps before they progress. Screening options include colonoscopy, which allows direct visualization and polypectomy in the same procedure, stool-based tests such as the fecal immunochemical test, and CT colonography, with the appropriate interval depending on the modality chosen and individual risk factors, including family history and certain hereditary syndromes such as Lynch syndrome.

Presenting symptoms of established colorectal cancer can include rectal bleeding, change in bowel habits, unexplained iron deficiency anemia, and unintentional weight loss, though early-stage disease detected through screening is often asymptomatic. Diagnosis is confirmed by biopsy at colonoscopy, and staging relies on CT imaging of the chest, abdomen, and pelvis to assess for metastatic spread, most commonly to the liver and lungs, along with pathologic assessment of the surgical specimen.

Surgical resection remains the primary treatment for localized disease, with adjuvant chemotherapy, often a regimen such as FOLFOX combining fluorouracil, leucovorin, and oxaliplatin, offered for higher-stage tumors to reduce recurrence risk. Metastatic disease is managed with systemic chemotherapy, frequently combined with targeted agents directed against pathways such as VEGF or EGFR depending on tumor molecular profile, and selected patients with limited liver metastases may benefit from surgical or ablative liver-directed therapy.""",
    },
    {
        "specialty": "oncology",
        "title": "Prostate Cancer: PSA Testing and Risk Stratification",
        "body": """Prostate cancer is the most common non-cutaneous malignancy diagnosed in men, arising from the glandular epithelium of the prostate and frequently detected incidentally or through prostate-specific antigen (PSA) screening, an enzyme produced by both benign and malignant prostate tissue whose blood levels can be elevated by cancer, benign prostatic hyperplasia, prostatitis, or recent instrumentation. Because PSA lacks specificity for malignancy, screening decisions involve shared decision-making that weighs the potential benefit of early detection against the risk of overdiagnosis and overtreatment of indolent tumors that may never cause symptoms.

When PSA is elevated or a nodule is felt on digital rectal examination, further evaluation with multiparametric MRI and image-guided or systematic prostate biopsy establishes the diagnosis and grade. Tumor aggressiveness is characterized using the Gleason score, which sums the two most prevalent histologic growth patterns observed under the microscope, with higher combined scores indicating less differentiated, more aggressive disease; Gleason grading is increasingly reported alongside a simplified Grade Group system ranging from one to five.

Management is highly individualized based on risk stratification, ranging from active surveillance with serial PSA testing and repeat biopsy for low-risk, localized disease, to surgery (radical prostatectomy) or radiation therapy with or without androgen deprivation therapy for intermediate- and high-risk localized disease. Metastatic prostate cancer is typically managed with androgen deprivation therapy, often combined with newer androgen receptor pathway inhibitors, since prostate cancer growth is characteristically driven by androgen signaling.""",
    },
    {
        "specialty": "oncology",
        "title": "Principles of Cytotoxic Chemotherapy and Common Toxicities",
        "body": """Cytotoxic chemotherapy encompasses a broad class of agents that interfere with cellular replication and division, exploiting the relatively higher proliferation rate of malignant cells compared with most normal tissue, though this selectivity is imperfect and accounts for many treatment-related side effects. Major drug classes include alkylating agents, which damage DNA directly, antimetabolites such as methotrexate and fluorouracil, which interfere with nucleotide synthesis, and antimicrotubule agents such as paclitaxel, which disrupt the mitotic spindle required for cell division. Combination regimens exploiting agents with different mechanisms and non-overlapping toxicities are commonly used to improve efficacy while managing side effects.

Because chemotherapy also affects rapidly dividing normal tissues, common toxicities include myelosuppression, with resulting neutropenia raising the risk of serious infection, mucositis, alopecia, and nausea, the latter now substantially mitigated by modern antiemetic regimens combining agents such as 5-HT3 receptor antagonists, NK1 receptor antagonists, and corticosteroids. Febrile neutropenia, defined as fever occurring in a patient with a significantly reduced neutrophil count, is a medical emergency requiring prompt empiric broad-spectrum antibiotics due to the risk of rapid progression to sepsis.

Treatment plans typically alternate cycles of chemotherapy with recovery periods to allow normal tissues, particularly bone marrow, to regenerate between doses. Growth factor support, such as filgrastim, may be used to reduce the duration and severity of neutropenia in regimens with significant myelosuppressive potential, and dose adjustments are routinely made based on observed toxicity and laboratory monitoring.""",
    },
    {
        "specialty": "oncology",
        "title": "Hodgkin and Non-Hodgkin Lymphoma: Overview",
        "body": """Lymphomas are malignancies of lymphocytes that are broadly divided into Hodgkin lymphoma and non-Hodgkin lymphoma based on characteristic histologic and immunophenotypic features. Hodgkin lymphoma is defined by the presence of Reed-Sternberg cells, large abnormal B cells identified on lymph node biopsy, and often follows a predictable pattern of contiguous nodal spread, while non-Hodgkin lymphoma comprises a far more heterogeneous group of B-cell and T-cell neoplasms with variable behavior ranging from indolent to highly aggressive.

Painless lymphadenopathy is the most common presenting sign for both categories, and systemic "B symptoms," including fever, drenching night sweats, and unintentional weight loss, suggest more advanced or biologically aggressive disease. Diagnosis requires excisional or core needle biopsy of an involved lymph node for histopathology and immunophenotyping, since fine-needle aspiration alone often provides insufficient architecture to subclassify lymphoma accurately. Staging uses the Ann Arbor system, based on the number and location of involved nodal regions and the presence of extranodal or disseminated disease, typically assessed with PET/CT.

Classic Hodgkin lymphoma is highly curable with combination chemotherapy regimens such as ABVD, often with radiation for localized disease. Non-Hodgkin lymphoma treatment varies widely by subtype: indolent forms such as follicular lymphoma may be observed or treated with rituximab-based regimens, while aggressive forms such as diffuse large B-cell lymphoma are typically treated with curative-intent combination immunochemotherapy such as R-CHOP.""",
    },
    # ------------------------------------------------------------------
    # Pulmonology
    # ------------------------------------------------------------------
    {
        "specialty": "pulmonology",
        "title": "Asthma: Pathophysiology and Stepwise Management",
        "body": """Asthma is a chronic inflammatory airway disease characterized by variable and reversible airflow obstruction, bronchial hyperresponsiveness, and airway inflammation driven predominantly by eosinophilic and mast cell-mediated processes in most patients. Common triggers include allergens, respiratory infections, exercise, cold air, and irritant exposures, and typical symptoms include wheezing, chest tightness, cough, and dyspnea that characteristically fluctuate over time and are often worse at night or early morning. Spirometry demonstrating an obstructive pattern that improves significantly after bronchodilator administration supports the diagnosis.

Management follows a stepwise approach based on symptom frequency and control. Short-acting beta-agonists such as albuterol provide rapid relief of acute bronchospasm and are used as needed by nearly all patients, but current guidelines emphasize that most patients beyond the mildest category should also receive a controller medication, most commonly an inhaled corticosteroid, either alone or combined with a long-acting beta-agonist, to reduce airway inflammation and prevent exacerbations. Reliance on short-acting beta-agonists alone without anti-inflammatory therapy is now recognized as inadequate for most persistent asthma.

For patients with severe, poorly controlled asthma despite optimized inhaled therapy, biologic agents targeting specific inflammatory pathways, such as anti-IgE or anti-interleukin-5 therapies, may achieve substantial reductions in exacerbation frequency. Written asthma action plans, correct inhaler technique, and identification and avoidance of individual triggers remain essential components of comprehensive long-term management, alongside periodic reassessment of control and step-up or step-down of therapy as needed.""",
    },
    {
        "specialty": "pulmonology",
        "title": "Chronic Obstructive Pulmonary Disease: Diagnosis and Staging",
        "body": """Chronic obstructive pulmonary disease (COPD) is a progressive, largely irreversible airflow limitation resulting from chronic bronchitis, emphysema, or a combination of both, most commonly caused by long-term cigarette smoking, though occupational exposures and, less commonly, alpha-1 antitrypsin deficiency contribute to disease in some patients. Emphysema involves destruction of alveolar walls and loss of elastic recoil, while chronic bronchitis reflects chronic mucus hypersecretion and airway inflammation, and most patients have overlapping features of both processes.

Diagnosis requires spirometry demonstrating a post-bronchodilator FEV1/FVC ratio below 0.70, confirming persistent airflow obstruction that is not fully reversible, distinguishing COPD from asthma in most cases. The GOLD staging system classifies severity based on the degree of airflow limitation (FEV1 percent predicted) and further incorporates symptom burden and exacerbation history to guide treatment intensity. Common symptoms include chronic productive cough, exertional dyspnea, and, in advanced disease, hypoxemia and cor pulmonale.

Bronchodilators, including long-acting muscarinic antagonists such as tiotropium and long-acting beta-agonists, form the foundation of maintenance therapy, with inhaled corticosteroids added in patients with frequent exacerbations or an eosinophilic phenotype. Smoking cessation is the single most effective intervention to slow disease progression, and supplemental oxygen improves survival in patients with significant chronic hypoxemia. Pulmonary rehabilitation, vaccination against influenza and pneumococcus, and prompt treatment of acute exacerbations with bronchodilators, corticosteroids, and antibiotics when indicated round out comprehensive management.""",
    },
    {
        "specialty": "pulmonology",
        "title": "Pulmonary Embolism: Diagnosis and Anticoagulation",
        "body": """Pulmonary embolism (PE) occurs when a thrombus, most often originating in the deep veins of the legs or pelvis, dislodges and travels through the venous circulation to occlude a pulmonary artery or its branches, impairing gas exchange and potentially causing acute right ventricular strain. Risk factors include prolonged immobility, recent surgery, malignancy, pregnancy, estrogen-containing medications, and inherited or acquired hypercoagulable states, and clinical presentation ranges from mild dyspnea and pleuritic chest pain to hemodynamic collapse in massive PE.

Clinical probability scoring systems, such as the Wells score, help determine the appropriate diagnostic pathway; low-probability patients may be evaluated with a D-dimer blood test, which, if negative, has a high enough negative predictive value to reasonably exclude PE, while higher-probability patients typically proceed directly to CT pulmonary angiography, the current diagnostic standard, which directly visualizes filling defects within the pulmonary vasculature. Ventilation-perfusion scanning remains a useful alternative, particularly in patients with contraindications to iodinated contrast.

Hemodynamically stable patients are treated with anticoagulation, most often a direct oral anticoagulant such as apixaban or rivaroxaban, which prevents thrombus propagation and allows the body's endogenous fibrinolytic system to gradually resolve the clot. Patients with hemodynamic instability from massive PE may require systemic thrombolysis or catheter-based thrombectomy to rapidly restore pulmonary blood flow. Evaluation for an underlying provoking factor and consideration of the appropriate duration of anticoagulation, ranging from several months to indefinite therapy, follows the acute treatment phase.""",
    },
    {
        "specialty": "pulmonology",
        "title": "Obstructive Sleep Apnea and CPAP Therapy",
        "body": """Obstructive sleep apnea (OSA) is characterized by repeated episodes of partial or complete upper airway collapse during sleep, leading to intermittent hypoxemia, fragmented sleep architecture, and characteristic loud snoring with witnessed pauses in breathing, often reported by a bed partner. Risk factors include obesity, a narrow oropharyngeal airway, retrognathia, and male sex, and untreated OSA is associated with excessive daytime sleepiness, impaired concentration, and an increased long-term risk of hypertension, atrial fibrillation, and other cardiovascular complications.

Diagnosis is established through polysomnography, either performed in a sleep laboratory or, for appropriately selected patients, through validated home sleep apnea testing, which quantifies the apnea-hypopnea index, the number of apneic and hypopneic events per hour of sleep, used to classify severity as mild, moderate, or severe. Screening questionnaires, such as the STOP-BANG tool, help identify patients at elevated risk who warrant formal testing.

Continuous positive airway pressure (CPAP) therapy, which delivers pressurized air through a mask to splint the airway open and prevent collapse, is the first-line treatment for moderate to severe OSA and has been shown to improve daytime sleepiness and reduce cardiovascular risk when used consistently. Alternative options for patients unable to tolerate CPAP include mandibular advancement oral appliances for milder disease, positional therapy, weight loss, and, in select anatomically appropriate patients, upper airway surgery or hypoglossal nerve stimulation. Adherence remains the principal challenge in long-term OSA management, and appropriate mask fitting and patient education substantially improve tolerance.""",
    },
    {
        "specialty": "pulmonology",
        "title": "Interstitial Lung Disease and Pulmonary Fibrosis",
        "body": """Interstitial lung disease (ILD) refers to a heterogeneous group of disorders characterized by inflammation and progressive scarring of the lung parenchyma and interstitium, resulting in impaired gas exchange and restrictive physiology on pulmonary function testing. Causes are diverse and include connective tissue diseases such as rheumatoid arthritis and systemic sclerosis, occupational and environmental exposures such as asbestos or silica, hypersensitivity pneumonitis from organic antigen exposure, certain medications, and idiopathic pulmonary fibrosis, in which no identifiable cause is found despite thorough evaluation.

Patients typically present with progressive exertional dyspnea and a persistent dry cough, and examination often reveals fine bibasilar "Velcro-like" crackles on auscultation. High-resolution CT (HRCT) of the chest is central to diagnosis, with patterns such as usual interstitial pneumonia, characterized by peripheral, basal-predominant reticulation and honeycombing, helping distinguish idiopathic pulmonary fibrosis from other ILD subtypes and, in many cases, obviating the need for surgical lung biopsy. Pulmonary function testing typically shows reduced forced vital capacity and reduced diffusing capacity for carbon monoxide, reflecting the restrictive and gas-exchange impairment characteristic of fibrotic lung disease.

Management depends heavily on the underlying etiology: idiopathic pulmonary fibrosis is treated with antifibrotic agents such as pirfenidone or nintedanib, which slow the rate of lung function decline, while ILD related to autoimmune disease may respond to immunosuppressive therapy. Supplemental oxygen, pulmonary rehabilitation, and, in appropriate candidates with progressive disease, evaluation for lung transplantation are important components of comprehensive care.""",
    },
    {
        "specialty": "pulmonology",
        "title": "Pleural Effusion: Evaluation with Thoracentesis",
        "body": """Pleural effusion refers to the abnormal accumulation of fluid within the pleural space, the potential space between the visceral and parietal pleura, and can result from a wide range of cardiac, infectious, malignant, and inflammatory processes. On chest radiography, effusions classically blunt the costophrenic angle and may layer along the dependent lung base, while ultrasound offers superior sensitivity for small effusions and is routinely used to guide safe thoracentesis.

A central step in evaluating a new, unexplained effusion is diagnostic thoracentesis, in which fluid is sampled and analyzed using Light's criteria to classify the effusion as a transudate or exudate. Transudative effusions, typically caused by conditions such as heart failure, cirrhosis, or nephrotic syndrome that alter hydrostatic or oncotic pressure, generally do not require extensive further pleural fluid workup once the systemic cause is identified. Exudative effusions, which arise from increased capillary permeability or impaired lymphatic drainage, warrant further evaluation for infection, malignancy, or inflammatory causes, guided by additional pleural fluid studies including cell count and differential, glucose, pH, Gram stain and culture, and cytology.

A complicated parapneumonic effusion or empyema, suggested by a low pleural fluid pH, low glucose, or frank pus, typically requires tube thoracostomy drainage in addition to antibiotics, since infected fluid collections often fail to resolve with antibiotics alone. Large or recurrent malignant effusions may be managed with therapeutic thoracentesis, indwelling pleural catheters, or pleurodesis to control symptomatic reaccumulation.""",
    },
    # ------------------------------------------------------------------
    # Nephrology
    # ------------------------------------------------------------------
    {
        "specialty": "nephrology",
        "title": "Chronic Kidney Disease: Staging and Management",
        "body": """Chronic kidney disease (CKD) is defined by abnormalities of kidney structure or function, most commonly a reduced estimated glomerular filtration rate (eGFR) or the presence of albuminuria, persisting for three months or longer. Diabetes and hypertension are the two leading causes worldwide, causing progressive glomerular and tubulointerstitial injury, while glomerulonephritis, polycystic kidney disease, and recurrent obstruction account for a smaller proportion of cases. The KDIGO staging framework classifies CKD by both eGFR category, ranging from G1 (normal or high) to G5 (kidney failure), and albuminuria category, since both dimensions independently predict progression risk and cardiovascular complications.

Management centers on slowing progression and mitigating complications. Blood pressure control, often with an ACE inhibitor or angiotensin receptor blocker, reduces intraglomerular pressure and proteinuria and remains a cornerstone of therapy, particularly in patients with significant albuminuria. SGLT2 inhibitors have more recently demonstrated substantial kidney-protective effects across a range of CKD etiologies, including in patients without diabetes, and are now widely incorporated into standard management. Dietary sodium and protein moderation, avoidance of nephrotoxic medications such as NSAIDs, and careful dose adjustment of renally cleared drugs are additional important measures.

As CKD advances, complications such as anemia from reduced erythropoietin production, secondary hyperparathyroidism from disturbed calcium-phosphate metabolism, and metabolic acidosis require monitoring and targeted treatment. Patients approaching kidney failure require timely education about renal replacement options, including hemodialysis, peritoneal dialysis, and transplantation, to allow adequate preparation before advanced symptoms develop.""",
    },
    {
        "specialty": "nephrology",
        "title": "Acute Kidney Injury: Prerenal, Intrinsic, and Postrenal Causes",
        "body": """Acute kidney injury (AKI) is defined by a rapid decline in kidney function over hours to days, reflected by a rise in serum creatinine, a fall in urine output, or both, and is conventionally classified by anatomic mechanism into prerenal, intrinsic, and postrenal causes. Prerenal AKI results from reduced renal perfusion, due to volume depletion, heart failure, or systemic hypotension, without direct structural kidney damage, and is typically reversible with restoration of adequate perfusion if addressed promptly. Postrenal AKI arises from obstruction of urine outflow, such as from prostatic enlargement, nephrolithiasis, or pelvic malignancy, and is often identified with renal ultrasound demonstrating hydronephrosis.

Intrinsic AKI reflects direct damage to renal parenchyma, most commonly acute tubular necrosis from prolonged ischemia or nephrotoxin exposure, including certain antibiotics, iodinated contrast, and NSAIDs, but also includes acute interstitial nephritis, typically drug-induced, and various forms of glomerulonephritis. Urinalysis and microscopy can help distinguish these categories: muddy brown granular casts suggest acute tubular necrosis, while white blood cell casts and eosinophiluria may point toward interstitial nephritis.

Management focuses on identifying and correcting the underlying cause, optimizing volume status, avoiding further nephrotoxic exposures, and adjusting medication dosing for reduced clearance. Indications for urgent dialysis in severe AKI include refractory hyperkalemia, severe metabolic acidosis, volume overload unresponsive to diuretics, uremic symptoms such as encephalopathy or pericarditis, and certain toxic ingestions, remembered by the mnemonic AEIOU.""",
    },
    {
        "specialty": "nephrology",
        "title": "Nephrotic Syndrome: Mechanisms and Evaluation",
        "body": """Nephrotic syndrome results from significant damage to the glomerular filtration barrier, allowing excessive loss of protein, principally albumin, into the urine, and is defined by the combination of heavy proteinuria (generally greater than 3.5 grams per day in adults), hypoalbuminemia, peripheral edema, and often hyperlipidemia. The edema of nephrotic syndrome results from a combination of reduced plasma oncotic pressure from hypoalbuminemia and renal sodium retention, and can become quite severe, involving the periorbital region, extremities, and, in advanced cases, the abdominal cavity as ascites.

In adults, common causes include membranous nephropathy, focal segmental glomerulosclerosis, and diabetic nephropathy, while minimal change disease is the predominant cause in children and generally carries a favorable prognosis with corticosteroid treatment. Evaluation typically includes quantification of proteinuria through a urine protein-to-creatinine ratio or 24-hour urine collection, a comprehensive metabolic panel, lipid panel, and serologic testing directed at secondary causes such as lupus or diabetes, with kidney biopsy often required in adults to establish the specific underlying glomerular lesion and guide treatment.

Patients with nephrotic syndrome are at increased risk of venous thromboembolism due to urinary loss of anticoagulant proteins, and of infection due to loss of immunoglobulins, both of which warrant clinical vigilance. Treatment combines disease-specific immunosuppressive therapy, guided by biopsy findings, with supportive measures including ACE inhibitors or ARBs to reduce proteinuria, diuretics for edema, and lipid-lowering therapy, since nephrotic-range proteinuria itself independently predicts progressive kidney function decline over time.""",
    },
    {
        "specialty": "nephrology",
        "title": "Hyperkalemia: Recognition and Emergency Management",
        "body": """Hyperkalemia, an elevated serum potassium concentration, is a potentially life-threatening electrolyte disturbance because of its effects on cardiac membrane excitability and conduction. Common causes include reduced renal potassium excretion from acute or chronic kidney disease, medications such as ACE inhibitors, angiotensin receptor blockers, and potassium-sparing diuretics, adrenal insufficiency, and shifts of potassium out of cells due to acidosis, tissue breakdown, or certain medications. Laboratory pseudohyperkalemia from hemolysis during blood draw should always be considered and, when suspected, prompts a repeat sample before aggressive treatment.

Clinical manifestations are often absent until potassium reaches significantly elevated levels, at which point muscle weakness and cardiac conduction abnormalities can develop. Electrocardiographic changes progress in a generally predictable sequence as potassium rises: peaked T waves appear first, followed by PR interval prolongation and QRS widening, and, in severe cases, a sine-wave pattern that heralds imminent ventricular fibrillation or asystole, making the ECG an essential rapid bedside assessment tool.

Emergency management follows a structured sequence: intravenous calcium gluconate is given first to stabilize the cardiac membrane when ECG changes are present, without lowering serum potassium itself, followed by measures that shift potassium intracellularly, including insulin with concurrent dextrose and inhaled beta-agonists such as albuterol. Definitive potassium removal is then achieved through loop diuretics in patients with adequate kidney function, potassium-binding agents such as sodium zirconium cyclosilicate or patiromer, or emergent hemodialysis in patients with severe or refractory hyperkalemia, particularly in the setting of advanced kidney failure.""",
    },
    {
        "specialty": "nephrology",
        "title": "Nephrolithiasis: Evaluation and Management of Kidney Stones",
        "body": """Nephrolithiasis, the formation of kidney stones, occurs when urinary concentrations of stone-forming substances such as calcium, oxalate, and uric acid exceed their solubility, leading to crystal formation and aggregation within the urinary tract. Calcium oxalate stones are the most common type overall, though uric acid, struvite, and cystine stones occur less frequently and often point toward specific underlying metabolic or infectious conditions. Risk factors include inadequate fluid intake, high dietary sodium and animal protein intake, obesity, and certain metabolic disorders.

The classic presentation is acute, severe, colicky flank pain that may radiate to the groin as the stone migrates down the ureter, frequently accompanied by nausea, vomiting, and gross or microscopic hematuria. Noncontrast CT of the abdomen and pelvis is the most sensitive imaging study for detecting stones and assessing size, location, and the presence of hydronephrosis, though renal ultrasound is often used preferentially, particularly in pregnant patients, to avoid radiation exposure.

Most stones smaller than about 5 millimeters pass spontaneously with supportive care, including analgesia, hydration, and alpha-blocker therapy such as tamsulosin to facilitate ureteral passage. Larger stones or those causing persistent obstruction, infection, or refractory pain may require urologic intervention, including extracorporeal shock wave lithotripsy, ureteroscopy with laser lithotripsy, or percutaneous nephrolithotomy for large stone burdens. After an initial stone episode, metabolic evaluation and increased fluid intake are recommended to reduce recurrence risk, since recurrence is common without preventive measures.""",
    },
    {
        "specialty": "nephrology",
        "title": "Renal Replacement Therapy: Hemodialysis and Peritoneal Dialysis",
        "body": """When chronic kidney disease progresses to kidney failure, renal replacement therapy becomes necessary to remove metabolic waste products, correct electrolyte and acid-base derangements, and manage volume status that the native kidneys can no longer adequately regulate. The two principal dialysis modalities are hemodialysis, in which blood is circulated through an extracorporeal circuit and filtered across a semipermeable membrane against a dialysate solution, and peritoneal dialysis, in which the patient's own peritoneal membrane serves as the filtering surface using dialysate instilled into and drained from the abdominal cavity.

Hemodialysis is most commonly performed at a dialysis center three times weekly, requiring reliable vascular access, ideally a surgically created arteriovenous fistula, which offers lower infection and complication rates than a central venous catheter, though a fistula requires several weeks to months to mature before use. Peritoneal dialysis is typically performed at home, either manually several times daily (continuous ambulatory peritoneal dialysis) or overnight using an automated cycler, and offers greater flexibility and preservation of residual kidney function, but requires a functioning peritoneal cavity and the patient's ability to perform sterile technique to avoid peritonitis.

The choice between modalities depends on patient preference, comorbidities, home support, and vascular or peritoneal anatomy, and many patients are counseled on both options prior to starting dialysis. Kidney transplantation, when feasible, generally offers superior survival and quality of life compared with long-term dialysis and remains the preferred treatment for eligible patients with kidney failure.""",
    },
    # ------------------------------------------------------------------
    # Neurology
    # ------------------------------------------------------------------
    {
        "specialty": "neurology",
        "title": "Acute Ischemic Stroke: Time-Sensitive Diagnosis and Treatment",
        "body": """Acute ischemic stroke results from sudden interruption of blood flow to a portion of the brain, most commonly due to thrombotic or embolic occlusion of a cerebral artery, leading to tissue ischemia and, if flow is not restored, infarction. Common presenting signs include sudden unilateral weakness or numbness, facial droop, slurred speech, and visual disturbance, often recognized clinically using the FAST mnemonic (face, arm, speech, time), and the National Institutes of Health Stroke Scale (NIHSS) is used to quantify deficit severity and guide treatment decisions.

Noncontrast CT of the head is obtained emergently, primarily to exclude hemorrhage, since the treatments for ischemic and hemorrhagic stroke differ fundamentally. In eligible patients presenting within the appropriate time window from symptom onset, intravenous thrombolysis with a fibrinolytic agent such as alteplase or tenecteplase can dissolve the occluding clot and improve functional outcomes, though it carries a risk of symptomatic intracranial hemorrhage that must be weighed against expected benefit. For patients with large vessel occlusion, mechanical thrombectomy, in which a catheter-based device retrieves or aspirates the clot, has extended the treatment window for selected patients, particularly when advanced imaging demonstrates a favorable ratio of salvageable tissue to already-infarcted core.

After the acute phase, management focuses on secondary prevention through antiplatelet or anticoagulant therapy depending on the presumed mechanism, blood pressure and lipid management, and identification of the underlying cause, such as atrial fibrillation or carotid stenosis, alongside early initiation of rehabilitation services to maximize functional recovery.""",
    },
    {
        "specialty": "neurology",
        "title": "Epilepsy and Seizure Disorders: Classification and Antiseizure Therapy",
        "body": """A seizure is a transient episode of abnormal, excessive, or synchronous neuronal electrical activity in the brain, which may produce motor, sensory, autonomic, or cognitive symptoms depending on the region involved, while epilepsy refers to a chronic tendency toward recurrent, unprovoked seizures. Seizures are broadly classified as focal, arising from a localized network within one hemisphere and potentially spreading to become bilateral, or generalized, involving widespread networks from onset, with subtypes including tonic-clonic, absence, and myoclonic seizures.

Diagnostic evaluation typically includes a detailed clinical history, often supplemented by witness accounts, along with electroencephalography (EEG) to characterize interictal or ictal epileptiform activity, and brain MRI to identify structural causes such as mesial temporal sclerosis, prior stroke, or tumor. A single unprovoked seizure does not automatically warrant a diagnosis of epilepsy, which generally requires either two or more unprovoked seizures or a single seizure with a substantially elevated risk of recurrence based on imaging or EEG findings.

Antiseizure medications, such as levetiracetam, lamotrigine, and valproate, are selected based on seizure type, patient comorbidities, and side-effect profile, aiming for seizure freedom with minimal adverse effects using the lowest effective dose, ideally as monotherapy when possible. Status epilepticus, a prolonged seizure or series of seizures without full recovery between them, is a neurologic emergency requiring rapid treatment, typically beginning with intravenous benzodiazepines followed by a second-line antiseizure agent if seizures persist, given the risk of ongoing neuronal injury with prolonged seizure activity.""",
    },
    {
        "specialty": "neurology",
        "title": "Parkinson's Disease: Clinical Features and Dopaminergic Therapy",
        "body": """Parkinson's disease is a progressive neurodegenerative disorder resulting from loss of dopaminergic neurons in the substantia nigra, a midbrain structure critical to the regulation of voluntary movement, leading to the cardinal motor features of bradykinesia, resting tremor, rigidity, and postural instability. Non-motor symptoms, including anosmia, constipation, REM sleep behavior disorder, and depression, often precede the onset of motor symptoms by years and are increasingly recognized as integral to the disease rather than incidental findings.

Diagnosis remains primarily clinical, based on the characteristic motor examination findings and their response to dopaminergic therapy, since no blood test or routine imaging study definitively confirms the diagnosis, although specialized imaging can help exclude alternative parkinsonian syndromes in atypical presentations. Levodopa, combined with carbidopa to prevent peripheral conversion to dopamine and reduce side effects such as nausea, remains the most effective symptomatic treatment for the motor features of Parkinson's disease, though long-term use is often complicated by motor fluctuations and dyskinesias as the disease progresses.

Other pharmacologic options include dopamine agonists, monoamine oxidase type B inhibitors, and amantadine, often used earlier in the disease course or as adjuncts to levodopa. For patients with advanced disease and significant motor fluctuations despite optimized medication, deep brain stimulation, involving surgically implanted electrodes that modulate abnormal basal ganglia activity, can substantially improve motor symptoms and quality of life. Multidisciplinary care, including physical therapy and attention to non-motor symptoms, is an important component of long-term management.""",
    },
    {
        "specialty": "neurology",
        "title": "Multiple Sclerosis: Diagnosis and Disease-Modifying Therapy",
        "body": """Multiple sclerosis (MS) is a chronic autoimmune disease of the central nervous system in which the immune system attacks myelin, the insulating sheath surrounding nerve fibers, resulting in inflammatory demyelinating lesions disseminated across the brain and spinal cord. The disease most commonly follows a relapsing-remitting course at onset, characterized by discrete episodes of neurologic dysfunction followed by partial or complete recovery, though a substantial proportion of untreated patients eventually transition to a secondary progressive phase marked by gradual, steady decline.

Common presenting symptoms include optic neuritis with painful vision loss, sensory disturbances, limb weakness, and bladder dysfunction, reflecting the wide range of central nervous system pathways that can be affected. Diagnosis relies on demonstrating dissemination of demyelinating lesions in both space and time, most often established through brain and spinal cord MRI showing characteristic periventricular, juxtacortical, and spinal cord lesions, supported by cerebrospinal fluid analysis demonstrating oligoclonal bands not present in serum.

Disease-modifying therapies, including injectable agents such as interferon-beta, oral agents such as fingolimod and dimethyl fumarate, and high-efficacy infusion therapies such as natalizumab and ocrelizumab, aim to reduce relapse frequency and slow accumulation of disability by modulating or suppressing the aberrant immune response. Acute relapses causing significant functional impairment are often treated with high-dose corticosteroids to hasten recovery. Given the variability in disease course and treatment response, ongoing monitoring with periodic MRI and clinical assessment guides therapy adjustments over time.""",
    },
    {
        "specialty": "neurology",
        "title": "Migraine: Pathophysiology, Acute Treatment, and Prevention",
        "body": """Migraine is a primary headache disorder characterized by recurrent moderate to severe headache episodes, typically unilateral and pulsating in quality, often accompanied by nausea, photophobia, and phonophobia, and worsened by routine physical activity. A subset of patients experience aura, transient focal neurologic symptoms, most commonly visual, that precede or accompany the headache phase and are thought to reflect a wave of cortical spreading depression. The pathophysiology involves activation of the trigeminovascular system and release of vasoactive neuropeptides, including calcitonin gene-related peptide (CGRP), which has become an important target for newer therapies.

Acute treatment for mild to moderate attacks often begins with NSAIDs or acetaminophen, while moderate to severe attacks typically require a triptan, such as sumatriptan, which acts as a serotonin receptor agonist to constrict cranial vessels and inhibit neuropeptide release. Newer acute options include CGRP receptor antagonists ("gepants") for patients who cannot tolerate or do not respond to triptans, particularly those with cardiovascular contraindications to vasoconstrictive agents.

Preventive therapy is considered for patients with frequent or disabling attacks and includes traditional agents originally developed for other indications, such as beta-blockers, certain anticonvulsants like topiramate, and tricyclic antidepressants, as well as migraine-specific monoclonal antibodies targeting CGRP or its receptor, administered by monthly or quarterly injection. Identification and avoidance of individual triggers, such as poor sleep, dehydration, and certain foods, along with headache diaries to track patterns, complement pharmacologic prevention strategies.""",
    },
    {
        "specialty": "neurology",
        "title": "Alzheimer's Disease and Evaluation of Cognitive Decline",
        "body": """Alzheimer's disease is the most common cause of dementia, a syndrome of acquired, progressive decline in cognitive function severe enough to interfere with daily functioning, and is pathologically characterized by accumulation of extracellular amyloid-beta plaques and intracellular neurofibrillary tangles composed of hyperphosphorylated tau protein, leading to progressive neuronal loss, particularly in the hippocampus and temporoparietal cortex. Early clinical features typically include short-term memory impairment, with word-finding difficulty, disorientation, and impaired executive function emerging as the disease advances.

Evaluation of suspected dementia includes a detailed history, often obtained from both the patient and a close informant, cognitive screening tools such as the Mini-Mental State Examination or Montreal Cognitive Assessment, and laboratory testing to exclude reversible contributors to cognitive impairment, including thyroid dysfunction, vitamin B12 deficiency, and structural brain lesions identified on MRI or CT. Distinguishing Alzheimer's disease from other dementia subtypes, such as vascular dementia, dementia with Lewy bodies, and frontotemporal dementia, relies on the characteristic pattern and tempo of cognitive and behavioral symptoms, since management and prognosis differ meaningfully between these categories.

Symptomatic pharmacologic treatment includes cholinesterase inhibitors, such as donepezil, which modestly improve cognition and function by increasing synaptic acetylcholine availability, and memantine, an NMDA receptor antagonist typically added in moderate to severe disease. More recently, anti-amyloid monoclonal antibody therapies have been developed to target underlying disease pathology in early Alzheimer's disease, though their clinical benefit is modest and they require careful monitoring for imaging abnormalities related to treatment. Non-pharmacologic support, including caregiver education, safety planning, and structured routines, remains central to comprehensive dementia care.""",
    },
]


def slugify(title):
    """Lowercase the title and collapse every run of non-alphanumeric
    characters into a single hyphen, trimming leading/trailing hyphens.
    """
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(repo_root, "seed_corpus")
    os.makedirs(out_dir, exist_ok=True)

    counts = {}
    written = 0
    for article in ARTICLES:
        specialty = article["specialty"]
        title = article["title"]
        body = article["body"].strip()

        slug = slugify(title)
        filename = "{}-{}.md".format(specialty, slug)
        path = os.path.join(out_dir, filename)

        content = "# {title}\n\n{disclaimer}\n\n{body}\n".format(
            title=title, disclaimer=DISCLAIMER, body=body
        )

        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        counts[specialty] = counts.get(specialty, 0) + 1
        written += 1

    print("Wrote {} files to seed_corpus/".format(written))
    for specialty in sorted(counts):
        print("  {}: {}".format(specialty, counts[specialty]))


if __name__ == "__main__":
    main()
