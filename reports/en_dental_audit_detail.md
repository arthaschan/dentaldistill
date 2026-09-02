# 英文牙科子集内容级审计报告（v2）

## 检测方法

- 对 `data/en_dental/{train,val,test}.jsonl` 逐题跑 `dental_filter.dental_match`（v2）。
- R1 强牙科词（tooth/teeth/dental/gingivitis/periodontal/pulpitis/alveolar bone/…）→ 真牙科；
- 仅命中 R2「oral 口腔语境」（oral ulcer/oral candidiasis/oral cavity/…）而无 R1 → 边界题。
- 边界题是「全身病的口腔表现」（Behçet/SCID/多形红斑等），是否算牙科取决于对「牙科」的定义，
  故显式列出供审计方按定义复核，而非静默判定。

## 结果

- `train`: 仅 R2 边界题 37 题
- `val`: 仅 R2 边界题 4 题
- `test`: 仅 R2 边界题 9 题

## 边界题清单

- `train` uid=medqa_train_004190 source=medqa hits=['oral health']
  - A 20-year-old man is brought to the behavioral health clinic by his roommate. The patient’s roommate says that the patient has been looking for cameras that ali
- `train` uid=medqa_train_009182 source=medqa hits=['oral ulcer']
  - A 22-year-old man presents with multiple, target-like skin lesions on his right and left upper and lower limbs. He says that the lesions appeared 4 days ago and
- `train` uid=medqa_train_008606 source=medqa hits=['oral lesion']
  - A 46-year-old woman presents to your office with oral lesions as shown in Image A. On examination, you find that her back has flaccid bullae that spread when yo
- `train` uid=medqa_train_001115 source=medqa hits=['oral lesion']
  - A 55-year-old man comes to the physician because of fever, fatigue, dry cough, headache, and myalgia over the past week. Two days ago, he developed several pain
- `train` uid=medqa_train_008341 source=medqa hits=['oral cavit']
  - A 68-year-old woman comes to the physician with dysphagia and halitosis for several months. She feels food sticking to her throat immediately after swallowing. 
- `train` uid=medqa_train_009536 source=medqa hits=['oral cavit']
  - A 44-year-old woman comes to the physician because of a 3-week history of progressive pain while swallowing. She has the feeling that food gets stuck in her thr
- `train` uid=medqa_train_005490 source=medqa hits=['oral lesion']
  - A 40-year-old woman presents with a lack of concentration at work for the last 3 months. She says that she has been working as a personal assistant to a manager
- `train` uid=medqa_train_009731 source=medqa hits=['oral ulcer']
  - A 14-year-old Asian girl is brought to the physician because of a 6-week history of fatigue. During this period, she has had a 3-kg (6.6-lb) weight loss and int
- `train` uid=medqa_train_008910 source=medqa hits=['oral candid']
  - A 3-month-old boy presents to his pediatrician with persistent diarrhea, oral candidiasis, and signs and symptoms of respiratory syncytial virus (RSV) pneumonia
- `train` uid=medqa_train_004088 source=medqa hits=['Oral ulcer']
  - A 22-year-old woman comes to the physician because of a 1-month history of persistent abdominal cramping, diarrhea, and rectal pain. During the past 2 weeks, sh
- `train` uid=medqa_train_002568 source=medqa hits=['oral candid']
  - A 16-year-old girl presents to her physician with itching, soreness, and irritation in the vulvar region. She reports that these episodes have occurred 6–7 time
- `train` uid=medqa_train_006055 source=medqa hits=['oral cavit']
  - A 35-year-old man is admitted with an acute onset of dysphagia, odynophagia, slight retrosternal chest pain, hypersalivation, and bloody sputum. These symptoms 
- `train` uid=medqa_train_007690 source=medqa hits=['oral ulcer']
  - A 7-year-old girl is brought to the physician with complaints of erythema and rashes over the bridge of her nose and on her forehead for the past 6 months. She 
- `train` uid=medqa_train_001835 source=medqa hits=['oral lesion', 'oral lesion']
  - A 40-year-old man presents with a rash, oral lesions, and vision problems for 5 days. He says the rash started as a burning feeling on his face and the upper pa
- `train` uid=medqa_train_000563 source=medqa hits=['oral ulcer']
  - A previously healthy 13-year-old girl is brought to the physician for evaluation of a 2-month history of fatigue. She reports recurrent episodes of pain in her 
- `train` uid=medqa_train_008591 source=medqa hits=['oral thrush']
  - A 66-year-old man is transferred to from another hospital after 3 days of progressively severe headache, vomiting, low-grade fever, and confusion. According to 
- `train` uid=medqa_train_000467 source=medqa hits=['oral ulcer', 'oral lesion']
  - A 24-year-old woman of Ashkenazi Jewish descent presents with recurrent bloody diarrhea and abdominal pain. She says she feels well otherwise. Review of systems
- `train` uid=medqa_train_008641 source=medqa hits=['oral ulcer']
  - A 35-year-old woman comes to the physician for the evaluation of fatigue over the past 6 months. During this period, she has also had fever, joint pain, and a r
- `train` uid=medqa_train_005221 source=medqa hits=['oral thrush']
  - A 2-year-old boy is brought to the physician for the evaluation of fever, breathing difficulty, and cough during the past week. In the past year, the patient wa
- `train` uid=medqa_train_009109 source=medqa hits=['oral ulcer']
  - A 33-year-old comes to her dermatologist complaining of a rash that recently started appearing on her face. She states that over the past three months, she has 
- `train` uid=medqa_train_005049 source=medqa hits=['oral cavit', 'oral hygiene']
  - A 36-year-old man presents with soreness and dryness of the oral mucosa for the past 3 weeks. No significant past medical history. The patient reports that he h
- `train` uid=medqa_train_001164 source=medqa hits=['oral health']
  - A 34-year-old man presents to the behavioral health clinic for an evaluation after seeing animal-shaped clouds in the form of dogs, cats, and monkeys. The patie
- `train` uid=medqa_train_001221 source=medqa hits=['oral candid']
  - A 32-year-old man comes to the physician for a follow-up examination 1 week after being admitted to the hospital for oral candidiasis and esophagitis. His CD4+ 
- `train` uid=medqa_train_007540 source=medqa hits=['Oral candid']
  - A 46-year-old woman presents to your medical office complaining of ‘feeling tired’. The patient states that she has been having some trouble eating because her 
- `train` uid=medqa_train_009932 source=medqa hits=['oral thrush']
  - A 25-year-old male graduate student is brought to the emergency department for respiratory distress after he was found by his roommate coughing and severely sho
- `train` uid=medqa_train_003232 source=medqa hits=['oral thrush']
  - A six-month-old infant presents with chronic, persistent diarrhea, oral thrush, and a severe diaper rash. The infant was treated four weeks ago for an upper res
- `train` uid=medqa_train_006871 source=medqa hits=['oral thrush']
  - A 25-day-old newborn is brought to the pediatrician for lethargy, poor muscle tone, and feeding difficulty with occasional regurgitation that recently turned in
- `train` uid=medqa_train_001921 source=medqa hits=['oral cavit']
  - A 72-year-old man has been recently diagnosed with stage 3 squamous cell carcinoma of the oral cavity. After the necessary laboratory workup, concurrent chemora
- `train` uid=medqa_train_009782 source=medqa hits=['oral ulcer']
  - A 28-year-old man comes to the physician for the evaluation of five episodes of painful oral ulcers over the past year. During this period, he has also had two 
- `train` uid=medqa_train_008724 source=medqa hits=['Oral thrush']
  - A 43-year-old HIV positive male presents with signs and symptoms concerning for a fungal infection. He is currently not on antiretrovirals and his CD4 count is 
- `train` uid=medqa_train_003551 source=medqa hits=['oral cavit']
  - A 45-year-old man comes to the physician for the evaluation of painful swallowing and retrosternal pain over the past 2 days. He was recently diagnosed with HIV
- `train` uid=BoF-2.13 source=BoF hits=['oral cancer']
  - Which one of the following is not a risk factor for oral cancer? A Smoking
B Alcohol
C Previous trauma to the site
D Social deprivation
E Betel nut chewing
- `train` uid=BoF-5.5 source=BoF hits=['oral carcinoma']
  - Which one of the following statements regarding carcinoma of the 5.6 5.7 lip is true? A It is commoner on the lower lip
B It is often caused by chewing betel nu
- `train` uid=BoF-5.36 source=BoF hits=['Oral candid']
  - Which one of the following is not an acquired white spot lesion? A Keratosis traumatica
B Smoker's keratosis
C Hairy leukoplakia
D Oral candidiasis
E White spon
- `train` uid=BoF-6.25 source=BoF hits=['Oral hygiene']
  - If a patient has a BPE score of 2, what is the correct course of treatment? A Nothing
B Oral hygiene instruction (OHI)
C OHI and scaling
D OHI, scaling and corr
- `train` uid=BoF-10.40 source=BoF hits=['Oral cancer']
  - A 25-year-old Asian man presents with fever, night sweats and cervical lymphadenopathy. What is the likely diagnosis? A Oral cancer
B Human immunodeficiency vir
- `train` uid=NBDE-Oral-49 source=NBDE hits=['oral health']
  - The “willful failure of parent or guardian to seek and follow-through with treatment necessary to ensure a level of oral health essential for adequate function 
- `val` uid=medqa_train_009262 source=medqa hits=['oral health']
  - A 26-year-old man presents to the behavioral health clinic for assistance overcoming his fear of public speaking. He has always hated public speaking. Two weeks
- `val` uid=medqa_train_000331 source=medqa hits=['oral cavit']
  - A previously healthy 46-year-old woman comes to her physician because of an itchy rash on her legs. She denies any recent trauma, insect bites, or travel. Her v
- `val` uid=medqa_train_001510 source=medqa hits=['oral thrush']
  - A 1-year-old girl is brought to the physician for follow-up examination 1 week after admission to the hospital for bacterial pneumonia. She has had multiple epi
- `val` uid=medqa_train_001836 source=medqa hits=['oral thrush']
  - A 2-year-old boy is brought to the physician for the evaluation of fever, difficulty breathing, and coughing for the past week. In the past year, he has had fou
- `test` uid=medqa_test_000037 source=medqa hits=['oral candid']
  - A 3-month-old boy presents to his pediatrician with persistent diarrhea, oral candidiasis, and signs and symptoms suggestive of respiratory syncytial virus (RSV
- `test` uid=medqa_test_000209 source=medqa hits=['oral cavit']
  - A 58-year-old white man with hypertension and type 2 diabetes mellitus comes to the physician because of a 3-month history of a painless lesion on his lower lip
- `test` uid=medqa_test_000488 source=medqa hits=['oral cavit']
  - A 38-year-old woman presents with eye dryness and a foreign body sensation in the eyes. On physical examination, the oral cavity shows mucosal ulceration and at
- `test` uid=medqa_test_000497 source=medqa hits=['Oral ulcer']
  - A 29-year-old woman presents to the physician with a blurred vision of her right eye for 2 days. She has pain around her right eye during eye movement. She take
- `test` uid=medqa_test_000939 source=medqa hits=['oral cavit']
  - A 32-year-old woman comes to the physician because of fatigue and joint pain for the past 4 months. Examination shows erythema with scaling on both cheeks that 
- `test` uid=medqa_test_001097 source=medqa hits=['Oral ulcer']
  - A 34-year-old man comes to the physician because of a 3-week history of colicky abdominal pain and diarrhea. He has bowel movements 10–12 times daily; the stool
- `test` uid=medqa_test_001111 source=medqa hits=['oral cavit']
  - A 3-year-old boy presents with episodic diarrhea with malodorous stools, stunted growth, occasional abdominal cramps, and an itchy rash. His mother says that th
- `test` uid=medqa_test_001208 source=medqa hits=['oral candid']
  - Which of the following patient presentations seen in a pediatric immunology clinic is most consistent with a diagnosis of Bruton's agammaglobulinemia? A. A 15-m
- `test` uid=mmlu_professional_medicine_test_000109 source=mmlu hits=['oral lesion']
  - A 55-year-old man comes to the physician because of a 2-week history of recurrent, widespread blister formation. Physical examination shows lesions that are mos
