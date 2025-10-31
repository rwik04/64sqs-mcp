import os
import sys

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from tools.content_writer.config import Config as config
from tools.content_writer.services.content_service import get_content, create_doc_from_content, create_html_from_content

class ContentWriter:
    def __init__(self):
        self.model_type = "gpt-4.1"
        self.api_key = config.OPENAI_API_KEY

    def create_draft(self,target_document_type, target_document_length, target_document_brief, notes):
        """
        Given a bunch of notes and the specs for the target document, this function should generate a content draft and return it as output
        Following are the details for each input paramater
        1. notes: List
        2. target_document_type: 'ppt' or 'doc' or 'html'
        3. target_document_length: 'XX slides' or 'XX words'
        4. target_document_brief: string
        """
        print("Creating Draft From Highlights")
        draft_content, draft_name, token_tracker = get_content(
            notes = notes,
            target_document_type = target_document_type,
            target_document_length = target_document_length,
            target_document_brief = target_document_brief,
            model_type = self.model_type,
            api_key = self.api_key
        )

        if target_document_type == "doc":
            create_doc_from_content(draft_content = draft_content, draft_name = draft_name)
        elif target_document_type == "html":
            create_html_from_content(draft_content = draft_content, draft_name = draft_name)
        else:
            print("Invalid target document type")

        print(f"{target_document_type} has been created. Token costs invoked")
        print(token_tracker)

if __name__=="__main__":
    writer = ContentWriter()

    # Create a list of notes from highlights data
    notes = [
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "US"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "US"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "US"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "US"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "US"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "US"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "India"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Country represented by the doctor (US, India, Germany).",
    "filename": "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Germany"
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Olivia Davis described the hospitals as being under significant strain during the pandemic. She noted that hospitals were overwhelmed and initially focused on patient care, which made data-sharing and coordination challenging. Specific bottlenecks mentioned included the lack of standardized reporting systems, fragmented data-sharing due to different EHRs and reporting standards, and the need to establish real-time dashboards for bed visibility to efficiently direct patients and allocate resources like ventilators and PPE. Additionally, she highlighted workforce challenges, such as the loss of skilled epidemiologists and public health nurses due to burnout and political attacks, emphasizing the need to rebuild the workforce and restore respect for public service."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Vogel described Germany's hospitals as having robust ICU capacity, which contributed to lower mortality rates compared to other European countries. He did not specifically mention ICU shortages, supply chain issues, or staff burnout as major bottlenecks. However, he did note that early models predicted potential hospital overload with wide uncertainty, and that avoiding healthcare system collapse was a shared objective among policymakers and health officials. Bureaucratic slowness, particularly in digital contact tracing and vaccination logistics, was mentioned as a challenge, but not specifically as a hospital bottleneck."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anderson described the hospitals as being under significant strain during the pandemic, especially in the initial weeks. He detailed several specific bottlenecks: ICU capacity had to be rapidly expanded by converting other hospital areas, but the main constraint was a shortage of trained ICU staff such as nurses and respiratory therapists. Supply chain issues were also prominent, with shortages of N95 masks and gowns requiring conservation strategies. Staff burnout and moral burden were significant, with efforts made to support staff wellbeing through rotations, rest areas, and mental health resources, though the emotional toll remained profound."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Brandt described the hospitals as being under significant strain during the pandemic. She noted an overwhelming surge in psychological distress, with a 60% increase in referrals by April 2020, and highlighted that even regular patients with previously stable conditions began relapsing. The hospital had to rapidly adapt by shifting to telepsychiatry and setting up an emergency hotline that received nearly 10,000 calls in three months. Staff burnout was specifically mentioned as epidemic by mid-2021, with healthcare workers suffering from moral injury, insomnia, and emotional distress. The hospital responded by creating peer-support groups, confidential counseling, and resilience workshops for staff. Dr. Brandt emphasized that systemic changes, such as improved staffing, breaks, and rest, are necessary for sustainable prevention of burnout. However, there was no mention of ICU shortages or supply chain issues in the provided text."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Roberts described the early phase of the pandemic as \"controlled chaos,\" indicating that hospitals were under significant strain. She mentioned that protocols had to be built from scratch, PPE supplies were tight, and there were daily uncertainties about the virus. Specific bottlenecks included PPE shortages, which led to creative solutions like reusing and sterilizing N95 masks, 3D-printed face shields, and fabric gowns made by community volunteers. Staff burnout was also a major issue, with colleagues lost to exhaustion, anxiety, and even suicide. The hospital implemented structured decompression programs, onsite counseling, peer support groups, and leadership transparency to help sustain the team. While ICU shortages were not explicitly mentioned, the overall description points to a system under considerable pressure, with supply chain issues and staff burnout as key challenges."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Siddharth Rao described the healthcare system in Bengaluru, India, as being under significant strain during the pandemic, especially during the Delta wave. Hospitals faced overwhelming numbers of COVID patients, with his 1000-bed hospital having 700 COVID patients at one point. Specific bottlenecks included oxygen shortages, which affected even tertiary hospitals, forcing difficult triage decisions about oxygen allocation. Staff burnout was also a major issue, with healthcare workers wearing PPE for extended hours in extreme heat, and several senior nurses being hospitalized themselves. The hospital implemented rotation breaks and psychological support to help manage morale. Dr. Rao also highlighted the importance of supply chain preparedness, noting that ventilators are useless without oxygen and logistics. Despite these challenges, the healthcare system rapidly expanded capacity, including oxygen plants and ICU networks, but the experience underscored the need for ongoing preparedness and multidisciplinary integration."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Schneider described the hospital system as being under significant strain during the pandemic, but also highlighted rapid adaptation and expansion efforts. The hospital expanded ICU capacity quickly and repurposed wards for intermediate respiratory care. Specific bottlenecks mentioned included the intense workload on staff, with Dr. Schneider describing brutal schedules and the need to balance research and clinical duties. Staff burnout and mental health were significant issues, with many staff living in hotel rooms to protect their families and every shift feeling existential. Leadership responded by instituting rotating rest weeks, mental health check-ins, and peer support. There is no mention of supply chain issues in the provided text."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Johnson described the healthcare system, particularly primary care clinics, as experiencing significant strain during the pandemic. She noted that the initial weeks were chaotic, with a rapid drop in clinic visits and a scramble to implement remote care due to minimal telehealth infrastructure. Major challenges included inequities in access to care, especially for vulnerable populations, and the need for creative outreach and resource distribution. Staff wellbeing was a concern, with primary care staff experiencing moral distress and burnout, leading to the implementation of rotating schedules, capped high-intensity shifts, and peer-support groups. While Dr. Johnson did not specifically mention ICU shortages or supply chain issues in hospitals, she did highlight the need for stockpiles of essential outpatient supplies and the importance of protecting staff with PPE. The overall picture is one of a system under considerable strain, particularly in outpatient and community settings, with staff burnout and resource challenges as key bottlenecks."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anjali Singh described the healthcare system, particularly pediatric care, as being under significant strain during the pandemic. She highlighted several bottlenecks: the need to set up separate pediatric COVID units, the emotional and logistical challenges of isolating children from their parents, and the difficulties of providing care while wearing PPE, especially in neonatal ICUs. Staff burnout was addressed through rotating shifts and emotional support systems, such as weekly team check-ins and open debriefings. She also noted that pediatric preparedness was initially lacking, with shortages of child-sized masks, ventilators, and appropriate medication doses. The experience underscored that emergency planning often overlooks the unique needs of children, and that pediatricians had to adapt rapidly to fill these gaps."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Ravi Kumar described the hospitals as being under significant strain during the pandemic, especially during the Delta wave. Initially, the hospital had to rapidly expand ICU capacity, running over 300 ICU beds—triple the normal capacity—and later adding 100 more step-up beds. Major bottlenecks included shortages of PPE, unclear protocols, and a lack of skilled manpower, which required crash training and a \"buddy system\" for staff. Staff burnout was a serious issue, with exhausted staff collapsing between shifts and emotional burdens from witnessing frequent deaths. Supply chain issues, particularly with oxygen, were managed effectively through coordinated efforts, but the strain on resources and personnel was evident throughout the crisis."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Kavita Joshi described the early phase of the pandemic as a period of significant strain on India's healthcare system, particularly due to data uncertainty, limited testing capacity, and logistical challenges. She highlighted that in March 2020, there were only about 10 authorized testing labs in the country, which rapidly expanded to over 1,000 by July. The expansion required not just equipment but also reagents, data systems, and trained personnel, indicating supply chain and staffing bottlenecks. In rural areas, the main issues were delayed diagnosis and lack of oxygen, which contributed to higher mortality rates. Dr. Joshi also mentioned the emotional and physical exhaustion experienced by healthcare teams, with many working 18-hour days, some contracting COVID themselves, and the loss of colleagues, pointing to significant staff burnout. While she did not specifically mention ICU shortages, the overall picture is one of a system under considerable strain, facing multiple bottlenecks including logistics, data gaps, and workforce fatigue."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Weber described Germany's hospitals as initially well-prepared due to early action and a high number of ICU beds per capita, which provided resilience compared to other countries. However, she also highlighted significant bottlenecks and strains: ICU nurses were pushed beyond endurance, leading to burnout and resignations; there were early shortages of PPE due to reliance on imports, prompting a rapid increase in domestic production; and the psychological toll on healthcare workers was considerable, with many suffering silently and structured mental health support programs being introduced. She emphasized that while equipment like ventilators could be procured, experienced staff could not be replaced quickly, and that emotional preparedness is as important as material resources."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Thompson described rural hospitals as being under significant strain during the pandemic. He highlighted several specific bottlenecks: a lack of local ICU beds, which made rapid patient transfers challenging; oxygen supply logistics, as the hospital relied on cylinders and concentrators rather than large pipeline systems; and workforce shortages, with staff absences due to illness or quarantine having an outsized impact on the small team. Staff burnout was acute, with extended shifts and emotional toll leading to some clinicians and nurses leaving or reducing hours. Supply chain disruptions, especially for PPE and oxygen, required creative solutions such as conservation strategies, local manufacturing, and resource pooling. These challenges were compounded by late patient presentations, transfer delays, and pre-existing health disparities."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Fischer described the hospitals as being under significant strain during the pandemic, though certain aspects of the system, such as inter-hospital coordination and equipment supply, were relatively well-prepared. The main bottlenecks mentioned included triage uncertainty due to overlapping symptoms, overcrowding both in terms of beds and information, and especially staff shortages and burnout. While ventilator shortages were not a major issue, there was a critical lack of trained personnel to operate them, leading to nurses and paramedics working double shifts and even requiring support from retired clinicians and military medics. Emotional exhaustion and the need for psychological support were also highlighted as major challenges."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Neha Reddy described the hospitals as being under significant strain during the pandemic, especially during the Delta wave in April–May 2021. She highlighted several specific bottlenecks: initially, there were delays in testing due to limited access to RT-PCR, which improved once private labs were allowed. During the peak, there were overwhelming numbers of admissions, with every bed, ventilator, and oxygen outlet in use. The hospital faced a crisis around oxygen supply, requiring real-time monitoring, diversion of supplies, and community support to manage shortages. Staff burnout was also a major issue, with long hours, emotional exhaustion, and even loss of colleagues to infection and exhaustion. The hospital implemented measures like wellness pods and peer support to help staff cope."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Miller described the hospitals as being under significant strain during the pandemic, requiring rapid adaptation and expansion of capacity. He detailed several specific bottlenecks: ICU shortages necessitated doubling ICU beds and converting non-traditional spaces into care areas; the main bottleneck was not equipment but a shortage of trained ICU nurses, which led to the implementation of a team nursing model. Supply chain issues were also prominent, with the collapse of global supply chains and high PPE usage rates forcing the hospital to source from nontraditional suppliers and establish emergency stockpiles. Staff burnout was a major concern, addressed through wellness initiatives, adjusted scheduling, and mental health support, but many clinicians still left due to the psychological toll."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Priya Sharma described the hospitals in India, particularly during the Delta wave, as being under immense strain rather than well-prepared. She detailed overwhelming patient loads, with 400–500 admissions daily, overflowing ICUs, and severe shortages of oxygen, which required constant monitoring and emergency logistics. Specific bottlenecks mentioned included inadequate ICU beds, fragmented oxygen supply chains, insufficient biomedical equipment maintenance, and staff burnout. The emotional and physical toll on healthcare workers was significant, with many living in hospital quarters, experiencing exhaustion, and losing colleagues to the virus. The crisis exposed both the dedication of healthcare workers and the fragility of the healthcare infrastructure, highlighting the need for better preparedness, infrastructure investment, and support for staff well-being."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Mehta described the hospitals in India, particularly in Mumbai, as being under significant strain during the pandemic. He detailed how the first wave brought overflowing hospitals, confusion due to atypical symptoms, and shortages of PPE and testing. The second wave, driven by the Delta variant, was described as even worse, with ICU admissions skyrocketing, oxygen demand outpacing supply, and acute shortages even in tertiary hospitals. Specific bottlenecks mentioned included ICU and oxygen shortages, ventilator shortages, the need to convert hospital wings and parking areas into isolation wards and negative-pressure ICUs, and the emergence of a black market for oxygen and drugs. Staff burnout and trauma were also highlighted, with the hospital eventually setting up mental health support and debriefing sessions for staff. Dr. Mehta emphasized that doctors had to take on multiple roles, including logistics and counseling, due to the crisis."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Hoffmann described that her hospital, Frankfurt University Hospital, had to adapt quickly by designating an entire ward for pediatric COVID care and retraining staff in adult-style respiratory support, which was not common in pediatric settings. Initially, most pediatric cases were mild, but as more severe cases like MIS-C appeared, coordination with other specialties became necessary. She also mentioned that pediatric staff volunteered for adult COVID wards when shortages peaked, indicating strain and the need for flexibility. Emotional support for staff was prioritized through regular reflection sessions and support from child psychologists, highlighting concerns about staff burnout. She noted that early pandemic plans barely mentioned pediatrics, suggesting a lack of preparedness for pediatric needs. However, she did not specifically mention ICU shortages or supply chain issues."
  },
  {
    "query": "Healthcare System Preparedness: Did the doctor describe their country’s hospitals as well-prepared or under strain during the pandemic? Were specific bottlenecks mentioned, such as ICU shortages, supply chain issues, or staff burnout?",
    "filename": "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Meier described Germany's hospitals as initially well-prepared, with sufficient ventilators and protective gear, thanks to early and structured coordination, widespread PCR testing, and a strong laboratory network. However, as the pandemic progressed, specific bottlenecks emerged. The main challenges shifted from equipment shortages to staff shortages, particularly by late 2021, when staff burnout and fatigue became the primary bottleneck rather than ventilator or ICU bed shortages. The psychological toll on healthcare workers was significant, with long shifts, emotional strain, and the need for psychological support. The ICU system adapted through coordination and transparency, but informal triage and prioritization became necessary during peak demand. Overall, while the system was robust in terms of equipment and coordination, human resource limitations and burnout were major strains as the crisis continued."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Hoffmann discussed the use of digital tools in the form of a national pediatric COVID registry and the integration of data systems, noting that their digital registry now connects pediatric ICUs nationwide, which was something they lacked before the pandemic. This indicates an innovation and improvement in technological readiness during the crisis. However, there is no mention of telemedicine or data dashboards specifically. She also reflected that early pandemic plans barely mentioned pediatrics, suggesting a lack of preparedness in some areas, but the experience led to faster integration of data systems."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anderson discussed the use of digital tools and telemedicine during the pandemic. He described how tele-ICU technology was both sustainable and transformative, allowing intensivist expertise to be extended to smaller hospitals, enabling real-time monitoring and consultant support, and reducing unnecessary patient transfers. He also mentioned piloting AI tools for early warning signals, though these required local calibration and validation before being fully trusted. Additionally, structured virtual visitation programs using tablets and secure video platforms were implemented to facilitate communication between patients and families due to restricted visitation policies. While telehealth modalities became integral to care delivery, AI remained an assistive tool pending further validation. There was no explicit mention of data dashboards or a lack of technological readiness, but the references to rapid adoption and piloting of new technologies indicate a spirit of innovation and adaptation."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anna Weber discussed the significant role of digital tools and data dashboards during the pandemic. She highlighted the use of RKI dashboards, digital contact tracing apps like the Corona-Warn-App, and interoperable hospital databases, which enabled near real-time surveillance and visualization of transmission patterns. However, she also noted that strict data privacy laws sometimes slowed integration, indicating a need for clearer frameworks for responsible data sharing in future crises. There was no specific mention of telemedicine, but the references to digital innovation and the challenges of technological readiness were clear."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Mehta discussed the use of a real-time oxygen dashboard during the pandemic, which was used to track oxygen flow rates and consumption in the hospital. He also mentioned the appointment of a central oxygen officer, a logistics engineer who worked around the clock to manage this data. Additionally, Dr. Mehta highlighted the need for a central digital health network linking public and private data for faster coordination, noting that the lack of such integration led to fragmentation and inefficiency. There was no specific mention of telemedicine, but the references indicate both innovative use of data dashboards and a recognition of technological gaps in the healthcare system."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Roberts discussed the significant role of digital tools and innovation during the pandemic. She highlighted the rapid advancement and adoption of digital tools such as real-time dashboards, EHR-linked analytics, and AI-assisted triage, noting that these technologies matured years ahead of schedule due to the crisis. She also emphasized the importance of data systems that could track infections, PPE usage, and staff exposures in near-real time, which strengthened hospital outbreak response. Additionally, Dr. Roberts mentioned the use of video calls as a vital communication tool for patients and families. Overall, she described the pandemic as a catalyst for accelerated collaboration and technological innovation in healthcare, breaking down traditional silos and fostering a culture of data-driven decision-making."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Brandt discussed the rapid adoption of telepsychiatry in response to the pandemic, noting that secure video consultations were set up within two weeks to address the surge in psychological distress. Initially, some patients were skeptical of digital tools, but many later found them to be a lifeline. An emergency hotline staffed by psychiatry residents and psychology interns was also established, handling nearly 10,000 calls in three months. Dr. Brandt highlighted that telemedicine, once a niche tool, became a permanent feature in psychiatric care. She did not specifically mention data dashboards, but emphasized that the pandemic fundamentally changed psychiatry in Germany by normalizing telemedicine and driving innovation in digital mental health services. There was no explicit mention of a lack of technological readiness, but the rapid shift to digital tools suggests adaptability and innovation."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Fischer discussed the significant role of technology and data during the pandemic. He described the development of a digital dashboard in Hamburg that tracked real-time hospital bed availability, oxygen status, and staffing, which allowed for efficient patient routing and served as a model for future emergencies. Telemedicine was also used to consult with rural hospitals on ventilation protocols, pushing emergency medicine into the digital era. Dr. Fischer emphasized that these technological innovations should become permanent, as pandemics are not the only crises that require such systems. There was no mention of a lack of technological readiness; rather, the focus was on rapid adoption and innovation."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Siddharth Rao discussed several ways technology and data were used during the pandemic. Tele-consultation became vital for following up with post-COVID cardiac patients, helping to reduce hospital exposure. The hospital also collaborated with a local health-tech startup to build predictive dashboards using anonymized EHR data, which allowed visualization of oxygen usage, patient deterioration risk, and ward occupancy predictions. Additionally, they piloted an AI tool to detect cardiac involvement from chest CT scans, which, while not perfect, showed promise. Dr. Rao noted that the pandemic accelerated the integration of medicine and data science by at least five years, highlighting significant innovation and increased technological readiness during the crisis."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Meier discussed the use of data dashboards and digital coordination tools during the pandemic. He highlighted the importance of Germany’s DIVI Intensive Care Registry, which tracked ICU bed availability nationwide and was updated daily by hospitals. This transparency and real-time data sharing were crucial for managing ICU capacity and patient transfers. Additionally, he mentioned the Robert Koch Institute’s real-time data dashboards, which served as a compass for hospitals. While there was no explicit mention of telemedicine or a lack of technological readiness, the references to data dashboards and digital coordination indicate significant use of digital tools and innovation in managing the crisis."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Vogel discussed the use of digital tools and data dashboards during the pandemic. He highlighted the development and deployment of the Corona-Datenspende app and the RKI's open dashboards, which were used to ensure data transparency and allow citizens access to the same data as policymakers. He also mentioned the challenge of integrating data from different federal states due to varying reporting systems, which necessitated rapid digital modernization. This led to the creation of the SurvNet 3.0 system, a real-time case and hospital surveillance platform, which he described as a significant technological achievement. Dr. Vogel acknowledged that Germany had postponed digital modernization prior to the pandemic, and COVID-19 forced the country to build a decade's worth of digital infrastructure in just ten months. There was no specific mention of telemedicine in the provided text."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Priya Sharma discussed the use of digital tools and data dashboards during the pandemic. She mentioned that technology groups built dashboards showing real-time availability of beds and oxygen, which played a crucial role in resource allocation. Additionally, the crisis accelerated modernization in healthcare, including digital monitoring and tele-ICU networks. However, she also highlighted gaps in technological readiness, such as inadequate biomedical equipment maintenance and the need for improved infrastructure. The pandemic forced investment in areas like local manufacturing of ventilators and digital systems, revealing both innovation and previous shortcomings in technological preparedness."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anjali Singh discussed the adoption of digital tools and telemedicine during the pandemic. She mentioned that telepediatrics became prominent, allowing consultations with children from distant villages, and that this model is likely to continue. Digital learning and telehealth were highlighted as new ways to reach rural families, including remote neonatal consults for smaller hospitals. These innovations were seen as positive changes accelerated by the crisis. However, she also pointed out initial gaps in pediatric preparedness, such as the lack of child-sized masks, ventilators, and doses, indicating some technological unpreparedness at the start of the pandemic."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Thompson discussed the use of digital tools and telemedicine during the pandemic. Telemedicine was described as a lifeline, especially for specialty consults such as cardiology and ICU care, allowing timely guidance and reducing unnecessary transfers. Tele-ICU consults enabled critical care specialists to assist remotely with ventilator management and complex decisions. Telehealth also expanded access for primary care follow-ups and mental health, though broadband limitations in some rural areas reduced its reach. Additionally, Dr. Thompson recommended investing in real-time bed dashboards for regional surge capacity and expanding broadband to enable telemedicine everywhere, highlighting both innovation and areas where technological readiness was lacking."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Ravi Kumar discussed the use of several digital tools and technological innovations during the pandemic. He described the implementation of a centralized dashboard for real-time tracking of oxygen usage, which allowed for rapid redistribution of resources. Tele-ICU systems were established using video conferencing tools to support remote hospitals, enabling consultants to guide peripheral doctors on critical care protocols. Additionally, automated monitoring dashboards and \"COVID communication corners\" (video booths for patient-family communication) were introduced. These innovations, some born out of necessity, have become permanent features. Dr. Kumar also highlighted the importance of data systems and technological readiness as key lessons for future preparedness."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Kavita Joshi discussed several technological innovations and the use of digital tools during the pandemic. She highlighted the ICMR COVID Data Portal, which integrated lab results nationwide and provided near real-time epidemiological data at a national scale. She also mentioned the CoWIN platform, which demonstrated India's ability to manage massive digital public health systems. Additionally, state-level data dashboards were used to help local officials plan resources such as oxygen, beds, and staff dynamically. Dr. Joshi emphasized that these tools were game-changers and should continue to be used beyond the pandemic for other public health challenges. There was no explicit mention of telemedicine in the provided text, nor was there a direct reference to a lack of technological readiness, but the rapid scaling and innovation in digital tools were clearly described as significant advancements during the crisis."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Schneider did not specifically mention the use of digital tools, telemedicine, or data dashboards during the pandemic in his interview. However, he did reference certain innovations and adaptations, such as the use of high-flow nasal oxygen, noninvasive ventilation, and the adoption of home-care oxygen and telemonitoring practices observed in Scandinavian centers, which were later adopted in Cologne's peripheral clinics. He also discussed the integration of research and clinical practice, the use of biomarkers and imaging for patient monitoring, and the importance of readiness for future pandemics. There was no explicit mention of technological readiness or lack thereof regarding digital health tools or data dashboards."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Neha Reddy discussed the significant role of technology and data during the pandemic. She described how her hospital built a digital triage dashboard that integrated test results, CT scores, and oxygen saturation to prioritize admissions. Telemedicine was also crucial, especially during the second wave, with over 3,000 teleconsults conducted daily for home isolation patients. Additionally, remote patient monitoring was implemented using Bluetooth-connected pulse oximeters linked to a central system, allowing proactive care. Dr. Reddy highlighted these innovations as transformative, turning reactive care into predictive care. She also noted the importance of data transparency and the integration of digital health infrastructure as key lessons and future directions for healthcare in India. There was no mention of a lack of technological readiness; rather, the focus was on rapid adaptation and innovation."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Miller discussed several aspects of technology and data use during the pandemic. He highlighted the rapid transition to telemedicine, noting that over 70% of outpatient visits were moved online within six weeks, demonstrating significant innovation and adaptability. He also described the development of real-time data dashboards to track bed occupancy, ventilator use, staff absences, and oxygen consumption, which enabled proactive decision-making. However, he pointed out challenges with technological readiness, particularly the difficulty of integrating disparate data systems like EHRs, HR software, and supply chain systems, emphasizing the need for better interoperability. Additionally, Dr. Miller mentioned the use of digital inventory dashboards with real-time analytics for supply chain management and the importance of maintaining these innovations post-pandemic."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Johnson discussed significant use of digital tools and telemedicine during the pandemic. She described how her clinic rapidly implemented telephone and video triage, set up remote-monitoring programs for patients isolating at home, and relied heavily on telemedicine to maintain continuity of care, especially for chronic disease management and triage of acute symptoms. She noted that telemedicine exposed inequities due to lack of broadband or devices among vulnerable populations, leading to hybrid approaches combining phone-based monitoring and community health worker check-ins. Dr. Johnson also highlighted operational innovations such as remote monitoring programs, hybrid care models, and the need for investments in broadband and device access. She acknowledged that the initial telehealth infrastructure was minimal, indicating a lack of technological readiness at the outset, but emphasized that several technological and operational innovations developed during the pandemic should be retained post-pandemic."
  },
  {
    "query": "Technology and Data Use: Did the doctor talk about using digital tools, telemedicine, or data dashboards during the pandemic? Were there references to innovation, or a lack of technological readiness?",
    "filename": "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Olivia Davis discussed significant use of digital tools and data dashboards during the pandemic. She described how her department initially struggled with fragmented, manual data collection methods, such as fax, spreadsheets, and handwritten forms, which made cohesive surveillance difficult. In response, they collaborated with Georgia Tech’s data science team to build a digital reporting system from scratch, leading to the development of semi-real-time dashboards tracking cases, test positivity, and hospital capacity. She also mentioned the creation of a real-time “bed visibility dashboard” for hospitals, which improved patient transfers and resource allocation. Dr. Davis highlighted the rapid digital acceleration in epidemiology, including automated data ingestion, real-time dashboards, and machine learning models for outbreak detection. She noted that the pandemic exposed a lack of technological readiness in public health, emphasizing the need for modernized, interoperable data systems and robust data pipelines as critical infrastructure."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Kavita Joshi explicitly mentioned experiencing professional and personal exhaustion, including working 18-hour days for months, sleeping in offices, and the emotional fatigue of analyzing death data daily. She also shared that many team members, including herself, contracted COVID-19 and that she lost two colleagues. As for coping mechanisms, she described that a sense of purpose and urgency kept the team going, as every dataset and decision felt meaningful in the context of saving lives. However, there was no explicit mention of institutional mental health support or formal coping programs."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Ravi Kumar explicitly discussed the emotional burden, fatigue, and distress experienced by healthcare workers during the pandemic. He described the relentless workload, daily exposure to death, and the loss of colleagues, which contributed to significant emotional strain. To help staff cope, the hospital set up a \"resilience room\" offering counseling services and rest pods, though Dr. Kumar noted that most support came from peer relationships and shared moments of small victories. After the Delta wave, a remembrance ceremony was held for staff who died in service, highlighting the collective emotional impact and the importance of institutional and interpersonal support mechanisms."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Siddharth Rao explicitly mentioned that burnout was universal among healthcare workers during the pandemic, describing the physical and emotional toll of wearing PPE for long hours and the hospitalization of senior nurses. He discussed coping mechanisms such as teamwork, rotation breaks, psychological support arranged by the hospital, and a ritual of ringing a bell to celebrate patient recoveries. These measures helped staff manage stress and maintain morale during challenging times."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Schneider explicitly mentioned significant staff burnout and emotional distress among healthcare workers during the COVID-19 response. He described how many pulmonary staff lived in hotel rooms to protect their families and that every shift felt existential. As coping mechanisms and institutional support, he discussed implementing rotating rest weeks, mental health check-ins, and peer support. He also emphasized the importance of leadership visibility, acknowledging small victories, and providing emotional sustenance by reminding staff of their purpose."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anderson explicitly discussed the emotional distress and moral burden experienced by healthcare workers during the COVID-19 pandemic, noting that maintaining quality under pressure was a daily achievement and that the moral burden of repeated deaths was profound and had lasting effects. He described institutional coping mechanisms and mental health support, such as prioritizing staff wellbeing with rotations to limit continuous exposure, dedicated rest areas, and mental health resources. He also emphasized the importance of normalizing mental health support for clinicians as a structural change for future preparedness."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Johnson explicitly discussed the emotional distress experienced by primary care staff during the pandemic, mentioning moral distress from watching patients suffer and concerns about bringing infections home. She described several coping mechanisms and institutional supports implemented to address staff wellbeing, including rotating schedules, capping high-intensity teletriage shifts, offering paid time off for rest, creating peer-support groups, and bringing in counselors for staff-led sessions. Additionally, measures were taken to protect administrative and nursing staff with clear PPE guidance and minimizing unnecessary exposure."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Brandt explicitly mentioned that healthcare workers experienced significant emotional distress, including burnout and fatigue. She described how many doctors and nurses suffered from 'moral injury,' guilt, insomnia, and being haunted by the experiences of patients dying alone. By mid-2021, burnout among healthcare workers was described as 'epidemic.' To support staff, the hospital implemented peer-support groups, confidential counseling, and resilience workshops focusing on mindfulness, breathing, and self-compassion rituals. Dr. Brandt emphasized that while these interventions helped, systemic changes such as improved staffing and rest are necessary for sustainable prevention."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Arjun Mehta explicitly mentioned burnout, fatigue, and emotional distress among healthcare workers during the COVID-19 pandemic. He described visible signs of trauma, such as tears in break rooms, insomnia, and guilt. As coping mechanisms, he noted that the hospital administration set up a mental health helpline and regular debriefing sessions, and that peer support became vital. Remembrance ceremonies for patients and staff lost to COVID were also held, which helped staff process grief. Dr. Mehta reflected that the pandemic forced Indian healthcare to confront the emotional side of medicine, which is often ignored."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Neha Reddy explicitly mentioned that burnout was universal among healthcare workers during the pandemic, describing long hours, emotional exhaustion, and moral distress. She noted that some colleagues were lost to infection and others to sheer exhaustion. As coping mechanisms, the hospital created 'wellness pods'—quiet spaces for meditation, naps, or just breathing freely without masks—and provided counseling support. However, Dr. Reddy emphasized that peer camaraderie was even more important. Additionally, moments of patient recovery and celebration helped refill their emotional reserves, highlighting the importance of finding meaning and humanity in their work during the crisis."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Meier explicitly discussed the emotional distress, fatigue, and psychological challenges faced by healthcare workers during the pandemic. He described the \"psychological weight of constant death, isolation, and uncertainty\" and noted that \"fatigue set in\" as the crisis continued. To cope, his team introduced decompression sessions—short debriefs at the end of shifts where staff could talk or sit in silence. Psychologists joined rounds weekly, and physical activities like yoga or music therapy were encouraged. Dr. Meier also mentioned personal coping mechanisms, such as keeping a personal log of emotions. These measures reflect both institutional and individual efforts to support mental health and manage burnout."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Thompson explicitly mentioned acute burnout among staff, noting that in a small hospital, each absence had an outsized impact. Staff worked extended shifts and often covered multiple roles, leading to significant emotional toll from losing patients and the pressure of transfer coordination. To cope, the hospital arranged peer support, confidential counseling, and community recognition events to help maintain morale. Despite these efforts, the cumulative stress led some clinicians and nurses to leave or reduce hours, which continues to affect the hospital."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Olivia Davis explicitly mentioned emotional exhaustion and burnout among public health professionals. She described the immense emotional exhaustion during the December 2020 surge, working 16-hour days and facing relentless case clusters. She also noted that thousands of skilled epidemiologists and public health nurses were lost due to burnout and political attacks, emphasizing the need to rebuild the workforce and restore respect for public service. However, there was no explicit discussion of coping mechanisms or the presence of institutional mental health support in her remarks."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. James Miller explicitly discussed burnout, fatigue, and emotional distress among healthcare workers. He described burnout as one of the biggest aftershocks of the pandemic, noting the psychological scars and the predictable outcome of empathy meeting exhaustion. To address these issues, the hospital launched a \"Wellness and Recovery\" initiative that included on-site counseling, peer-support hotlines, and decompression lounges staffed by mental health professionals. Additionally, they adjusted scheduling models to mandate rest windows, cap weekly ICU hours, and rotate staff between high- and low-intensity units, all as coping mechanisms and institutional mental health support."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Weber explicitly mentioned burnout and emotional distress among healthcare workers. She described how ICU nurses were pushed beyond endurance, leading to burnout and resignations by the second year. She also discussed the emotional toll, noting that many healthcare workers suffered silently and that post-traumatic stress among clinicians became a topic of discussion after the crisis. As coping mechanisms and institutional support, she detailed the introduction of structured psychological support programs, creation of 'Wellness Corners' (quiet rooms with coffee, music, and space to decompress), one-on-one sessions with psychologists, and flexible shifts for single parents. However, she acknowledged that despite these measures, many still struggled with expressing vulnerability and emotional distress."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Roberts explicitly mentioned burnout, fatigue, and emotional distress among healthcare workers, noting that colleagues were lost to exhaustion, anxiety, and even suicide. She described several coping mechanisms and institutional mental health supports that were implemented, including structured decompression programs (such as mandatory days off after ICU rotations), onsite counseling, peer support groups, and memorial spaces. She emphasized that leadership transparency and normalizing seeking help were crucial, and that the culture of stoicism in medicine had to shift towards vulnerability and empathy within teams."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Vogel did not explicitly mention burnout, fatigue, or emotional distress among healthcare workers. He described the work during the pandemic as the most intense, complex, and emotionally charged of his career, but did not specifically discuss the experiences of healthcare workers or reference institutional mental health support or coping mechanisms. The focus was more on the challenges faced by epidemiologists and public health advisors, including emotional aspects of their own work, rather than frontline healthcare staff."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anjali Singh explicitly mentioned the emotional distress and burnout experienced by healthcare workers during the pandemic. She described pediatric care as emotionally draining, especially during COVID, and noted the relentless nature of the work. To cope, her hospital implemented a rotating shift system to avoid burnout and encouraged open debriefing, telling residents that it was okay to cry. They also started weekly team check-ins focused on emotional wellbeing rather than medical briefings. She highlighted the crucial role of nurses, many of whom were young mothers caring for others' children while being away from their own families. These measures served as institutional support mechanisms to help staff manage stress and emotional fatigue."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Priya Sharma explicitly mentioned the immense physical and emotional toll experienced by healthcare workers during the COVID-19 pandemic. She described living in hospital quarters to avoid infecting families, the exhaustion from working in PPE during extreme heat, and the emotional grief from losing patients and colleagues. She discussed feelings of powerlessness and the accumulation of grief. Regarding coping mechanisms, she highlighted the importance of team solidarity, peer support, and small gestures like sharing food and celebrating patient recoveries. Institutional support included rotating rest weeks and counseling arranged by hospital administration, though she noted that peer support was what really helped most staff cope with burnout and stress."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Hoffmann did discuss emotional distress, fatigue, and the emotional impact on healthcare workers during the pandemic. She described how her team coped by creating spaces for reflection, such as weekly 'coffee rounds' where staff of all levels could share frustrations, fears, and exhaustion. She also mentioned partnering with child psychologists to help process grief, even when pediatric deaths were rare locally. Dr. Hoffmann emphasized the importance of taking care of caregivers and highlighted that supporting the emotional well-being of her team became essential during the crisis."
  },
  {
    "query": "Impact on Healthcare Workers: Did the doctor explicitly mention burnout, fatigue, or emotional distress? Did they discuss coping mechanisms or the presence of institutional mental health support?",
    "filename": "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Fischer explicitly discussed the emotional toll, fatigue, and distress experienced by healthcare workers during the pandemic. He described the emergency department as a \"pressure cooker of exhaustion and empathy\" and noted that \"the shortage was of rest and reassurance\" rather than just equipment. He recounted the emotional difficulty of making triage decisions under pressure and the lasting impact of those choices. As coping mechanisms, Dr. Fischer mentioned building small rituals of resilience, such as pausing for 30 seconds of silence after every resuscitation, and holding peer support circles every Friday for staff to vent, cry, or share dark humor. Sometimes a psychologist was invited, but mostly the team supported each other. He did not mention formal or institutional mental health support beyond these peer-led initiatives."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Mehta summarized several key lessons and provided recommendations for future pandemics. He emphasized that early diagnosis and access to oxygen are more effective in saving lives than high-end drugs, and highlighted the importance of public education about when to seek help. Teamwork and collaboration were major takeaways, as he noted that working across specialties, hospitals, and even industries proved that silos reduce efficiency. Communication was also stressed as critical, particularly in managing misinformation and fear. Dr. Mehta recommended systemic reforms, including strengthening public health capacity, building primary care networks for early intervention, and ensuring workforce protection with mental health support and hazard pay. He also advocated for a central digital health network to improve coordination. Overall, humility, compassion, and adaptability were underscored as essential qualities for healthcare professionals during a pandemic."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Thompson summarized several key lessons and provided recommendations for future pandemics. He emphasized the importance of investing in regional surge capacity, formal transfer agreements, real-time bed dashboards, and stockpiling oxygen infrastructure suited to rural settings. He also recommended expanding broadband for telemedicine, strengthening rural workforce pipelines, and building formal community partnerships into emergency planning, highlighting that nonprofit and faith-based organizations are central to rural response. In his final reflections, Dr. Thompson noted the fragility and resilience of rural healthcare, stressing that extraordinary teamwork and dedication were required from small teams. He called for policymakers to recognize the distinct needs of rural healthcare and to fund durable, long-term solutions rather than temporary fixes. Teamwork, communication, and preparedness were all underscored as major takeaways from his experience."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Vogel provided a clear summary of lessons learned and recommendations for future pandemics. He emphasized that preparedness must be actively practiced, not just planned, and that real-time data flow is crucial for effective decision-making. Communication was highlighted as an integral part of containment, with trust being essential for data to be effective. He also stressed the importance of permanent data infrastructures and training scientists to communicate uncertainty. Teamwork and collaboration were underscored, particularly in the context of Germany's federal structure and the need for coordinated action. Dr. Vogel reflected on the importance of humility, empathy, and remembering that epidemiological data represents real people, not just numbers."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Meier provided several key lessons and recommendations for future pandemics. He emphasized the importance of early laboratory preparedness, ICU coordination, and scientific rigor, noting that these factors saved lives. However, he also reflected that pandemic fatigue and the erosion of public compliance were underestimated, suggesting that future communication should be more emotionally intelligent and not just data-driven. Dr. Meier highlighted that resilience in healthcare depends on having sufficient staff, not just equipment, recommending a focus on training and retaining nurses and respiratory therapists. Teamwork was a major takeaway, as he stated that no one survives such a crisis alone and that the pandemic reinforced his belief in the necessity of collaboration. He also advised future healthcare professionals to prepare both their minds and hearts, underscoring that compassion and service are as vital as scientific knowledge during crises."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Hoffmann summarized several key lessons and recommendations for future pandemics. She emphasized that preparedness must explicitly include children, as early pandemic plans often overlooked pediatrics. Mental health was highlighted as an integral part of infection control, noting that isolation can be as damaging as disease itself. Communication was identified as crucial for compliance, with honest and clear explanations fostering cooperation among families. Dr. Hoffmann also stressed the importance of integrating data systems quickly, which led to the creation of a nationwide pediatric ICU registry. Teamwork and emotional support within her team were fostered through regular, hierarchy-free meetings and collaboration with psychologists. She recommended earlier investment in school ventilation and more unified public messaging to avoid confusion. Overall, teamwork, communication, and preparedness were major takeaways from her experience."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Kavita Joshi provided several key lessons and recommendations for future pandemics. She emphasized that accurate data is foundational for decision-making, advocating that \"data is infrastructure.\" She highlighted the importance of decentralizing public health, noting that district-level autonomy was crucial in saving lives. Preparedness was another major takeaway; she recommended that the infrastructure and systems developed during COVID-19 should not be dismantled but instead evolve into a permanent, all-hazard response system. Dr. Joshi also stressed the need for significant investment in field epidemiology training, stating that India requires many more skilled epidemiologists. In terms of communication, she underscored the necessity of transparency, unified messaging, and empathetic, data-backed public health communication. Teamwork and collaboration were celebrated as essential, with examples of cross-generational and cross-disciplinary cooperation. Finally, she reflected on the importance of combining scientific rigor with empathy, suggesting that compassion is as vital as data in public health leadership."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Miller provided several key lessons and recommendations for future pandemics. He emphasized the importance of flexibility over mere capacity, empowering staff, decentralizing decision-making, and investing in prevention. He highlighted that resilience is fundamentally about people, not just systems, and stressed the need to take care of the workforce. Teamwork was a major theme, as he described unprecedented collaboration among Boston's hospitals, including data sharing, patient transfers, and resource coordination. Communication was also underscored as vital, both for maintaining staff morale and public trust, with transparent, honest, and frequent updates being crucial. Preparedness was a central takeaway, with recommendations to maintain emergency stockpiles, diversify supply chains, and institutionalize innovations like command centers and telehealth. Leadership qualities such as clarity, humility, and empathy were identified as essential during crises."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anderson provided several key lessons and recommendations for future pandemics. He emphasized the importance of investing in workforce development and retention, creating flexible surge-capable staffing models with cross-training, ensuring regional coordination for critical supplies, establishing rapid-response trial networks, and normalizing mental health support for clinicians. He also highlighted the need to strengthen primary prevention and public health infrastructure. Teamwork and communication were major takeaways, as he described the extraordinary courage and compassion of healthcare teams, the use of multi-disciplinary committees, and the implementation of structured communication with families. Preparedness was a central theme, with recommendations for operational flexibility, rapid adaptation, and long-term policy improvements to address systemic weaknesses exposed by the pandemic."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Siddharth Rao summarized several key lessons and recommendations from the pandemic experience. He emphasized that integration and multidisciplinary teamwork are more effective than working in silos, as collaboration between departments saved lives. Preparedness, especially regarding supply chains for essentials like oxygen, was highlighted as crucial. He also stressed that trust—both in doctors and in data—is foundational for public health compliance. Teamwork was a major coping mechanism for staff morale and burnout, with rituals and mutual support helping them endure difficult times. Communication, particularly clear and data-backed messaging, was vital in combating misinformation and reassuring patients. Dr. Rao also reflected on the importance of humility, self-care for healthcare workers, and the need to maintain the momentum of healthcare system improvements made during the crisis."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Johnson provided several lessons learned and recommendations for future pandemics. She emphasized the importance of strengthening funding for community health centers, ensuring sustained reimbursement for telehealth, investing in broadband and device access for low-income patients, and formalizing partnerships between primary care and public health for rapid mobilization. She also highlighted the need for paid sick leave policies, worker protections, and stockpiling essential outpatient supplies. Teamwork and communication were underscored through her discussion of community partnerships, collaboration with public health, and hybrid care models involving community health workers. Preparedness was a major takeaway, with calls for health equity to be central in planning and for primary care to be recognized as foundational to health systems. Dr. Johnson stressed that investing in social supports, community-based care, and primary prevention will better protect communities in future emergencies."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Weber provided several key lessons and recommendations for future pandemics. She emphasized that preparedness must be dynamic and continuously updated with research and simulation drills. Communication was highlighted as life-saving, with the point that empathy, not just data, changes behavior. She also stressed the necessity of global cooperation, noting that effective pandemic response requires coordination across science, policy, and citizens. Teamwork was evident in her descriptions of rapid hospital adaptations, staff training, and psychological support programs. The importance of supporting healthcare workers' mental health and maintaining supply chain resilience were also underscored. Overall, Dr. Weber's reflections centered on the need for evolving preparedness, transparent and empathetic communication, and strong collaboration at all levels."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anjali Singh summarized several key lessons and recommendations for future pandemics. She emphasized that preventive care, such as immunizations and nutrition programs, should never be suspended, even during lockdowns. She advocated for greater investment in child mental health, recommending that every district have pediatric counselors. Dr. Singh also stressed the importance of including pediatricians in public health planning, highlighting that children's needs are unique and must be central in preparedness discussions. Teamwork and solidarity among healthcare workers were highlighted as major positives, with pediatricians from various sectors collaborating and supporting each other. Communication was also a major theme, both in countering misinformation through community outreach and in supporting the psychological wellbeing of staff through open debriefings and team check-ins. Preparedness was underscored by the need for child-specific resources and emergency planning that accounts for children's unique needs. Dr. Singh reflected that the pandemic redefined pediatric practice, making resilience, public health education, and digital wellbeing new priorities."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Schneider summarized several key lessons and recommendations for future pandemics. He emphasized the importance of anticipating not just alveolar but also vascular and endothelial components in lung injury, and advocated for biomarker-guided care to stratify patients. He stressed that post-COVID lung care, including fibrosis management, rehabilitation, and long-term follow-up, should become standard practice. Investing in clinician-researchers to bridge laboratory and bedside work was highlighted as crucial for accelerating insights. Dr. Schneider also underscored that readiness for respiratory pandemics must be treated as an ongoing duty, not a temporary project. Teamwork and communication were implicitly emphasized through his discussion of collaborative research pipelines, integration of care across specialties, and leadership strategies to support staff well-being and reduce burnout. He noted the value of visible leadership, peer support, and celebrating team successes as ways to sustain morale and resilience."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Ravi Kumar provided a clear summary of lessons learned and recommendations for future pandemics. He emphasized three main lessons: the importance of investing in infrastructure (such as oxygen plants, data systems, and training pipelines) before crises occur; strengthening workforce resilience through incentives, fair pay, and mental health support; and building public trust through transparency and science-led public health. Teamwork and communication were highlighted throughout his reflections, with examples such as the \"buddy system\" for ICU teams, tele-ICU support for remote hospitals, and the need for consistent public messaging. Preparedness was a major takeaway, as Dr. Kumar noted that it is not just a document but a living system requiring constant nurturing. He also reflected on the importance of leadership, humility, and the dedication of healthcare workers during the crisis."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Roberts provided several key lessons and recommendations for future pandemics. She emphasized that preparedness must be proactive, with continuous investment in surveillance, vaccine platforms, and public health infrastructure, rather than only during crises. Global cooperation, especially in data-sharing and manufacturing capacity, was highlighted as essential, along with stronger mandates and funding for organizations like the WHO. Locally, she advocated for treating public health as a matter of national security. Teamwork and communication were major takeaways: the pandemic accelerated collaboration across sectors, broke down silos, and embedded infection prevention as everyone's responsibility. Communication, both within teams and with the public, was described as vital, with transparency and empathy being crucial for building trust. Dr. Roberts also stressed the importance of multidisciplinary collaboration, humility, and compassion for future clinicians, underscoring that truth delivered with empathy is powerful medicine."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Helena Brandt reflected deeply on the lessons learned during the pandemic. She emphasized that compassion is the most advanced technology in medicine, highlighting the importance of presence, listening, and connection with patients. She noted that the pandemic stripped away the illusion of control but revealed the significance of human connection, stating that none of us were truly alone, just distanced. Dr. Brandt also observed that the crisis normalized telemedicine, blurred the boundaries between mental and physical health, and led to a historic cultural shift in Germany toward open discussions about mental health. She stressed that systemic changes, such as improved staffing, breaks, and rest, are necessary for sustainable prevention of burnout, especially among healthcare workers. While she did not explicitly use the terms teamwork or communication, her descriptions of peer-support groups, interdisciplinary rehabilitation clinics, and collaboration with social services all point to the critical role of teamwork and communication. She also recommended greater integration between psychiatry and primary care and recognized the need for ongoing healing and support as society recovers from collective exhaustion."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Olivia Davis provided several key lessons and recommendations for future pandemics. She emphasized the need for stable, year-round funding for public health, modernized and interoperable data systems, and workforce development to rebuild and support public health professionals. Teamwork and collaboration were highlighted as essential, particularly the breaking down of barriers between public health and clinical medicine, and the importance of daily coordination among epidemiologists, hospital administrators, and EMS directors. Communication was identified as both a major challenge and a critical tool, with the need for context, empathy, and trusted local voices to effectively reach communities. Preparedness was underscored by the need for robust data pipelines and digital infrastructure, as well as the importance of being proactive rather than reactive. Dr. Davis also reflected on the importance of leadership rooted in credibility, compassion, and trust-building during crises."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Priya Sharma summarized several key lessons and recommendations for future pandemics. She emphasized that public health infrastructure should be treated as national security, highlighting the need for robust oxygen plants, supply chains, and critical care capacity that do not rely on emergency improvisation. She also stressed the importance of data transparency and communication, noting that public trust depends on timely and honest information. Additionally, she called for long-term investment in healthcare worker protection and mental health, recognizing that sustained effort without rest or recognition is unsustainable. Teamwork was a major theme throughout her reflections, as she described the solidarity among healthcare workers and the crucial role of community and volunteer groups. Communication was also highlighted, both in countering misinformation and in supporting patients and families. Preparedness was underscored as not just stockpiling resources, but building adaptable systems. These lessons, she hopes, will drive reform and better preparedness for future crises."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Fischer did summarize key lessons learned and provided recommendations for future pandemics. He emphasized the importance of rapid reorganization, inter-hospital coordination, and evidence-based adaptability as major successes. He also highlighted the need for improved long-term workforce sustainability, including better rotation systems, psychological support, and incentives to retain staff. Teamwork and communication were central themes, as seen in the creation of a citywide emergency coordination cell and peer support circles for emotional resilience. Preparedness was underscored by the rapid transformation of the emergency department, the use of digital dashboards for real-time coordination, and the adaptability of protocols. Dr. Fischer reflected that heroism is quiet, and that medicine requires both scientific precision and empathy, stressing humility and the importance of carrying these lessons forward for future emergencies."
  },
  {
    "query": "Lessons and Reflections: Did the doctor summarize lessons learned or provide recommendations for future pandemics? Were teamwork, communication, or preparedness emphasized as major takeaways?",
    "filename": "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Neha Reddy provided a clear summary of lessons learned and recommendations for future pandemics. She emphasized the importance of decentralized healthcare capacity, data transparency, and public health literacy as key lessons. Teamwork and communication were highlighted through examples such as the creation of multidisciplinary task forces, the use of digital dashboards for coordination, and proactive public health communication to combat misinformation. Preparedness was underscored by the hospital's rapid adaptation, including setting up parallel infrastructure, micro-cohorting staff, and integrating technology for triage and remote monitoring. Dr. Reddy also reflected on the evolution of infectious disease medicine, noting its increased recognition and the shift towards data-driven, collaborative approaches. She stressed that public health is a culture that requires sustained education and that prevention should remain a priority even after the crisis fades."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anderson discussed vaccine hesitancy, noting that while vaccination dramatically reduced severe cases and shifted ICU admissions toward unvaccinated and immunocompromised patients, vaccine hesitancy in some communities continued to drive preventable severe disease. He expressed frustration among clinicians who witnessed the difference vaccination could make. However, there was no mention of specific communication efforts, vaccination drives, or strategies to improve public trust, nor was the spread of misinformation directly addressed."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Rao discussed both vaccine hesitancy and the spread of misinformation. He noted that after the vaccination rollout, severe cardiac-related COVID cases dropped significantly, and his team used internal data to reassure hesitant patients about vaccine safety, finding only two mild myocarditis cases among 60,000 vaccinated individuals. He also described the challenge of combating misinformation, such as myths about blood thinners and vaccines, which led to delays in patients seeking care. To address this, the hospital organized community webinars to provide clear, factual information about COVID, cardiac risks, and the benefits of vaccination, emphasizing that clear communication backed by data is crucial for public trust and compliance."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Hoffmann discussed vaccine hesitancy among parents, noting that many were understandably cautious and wanted long-term safety data before vaccinating their children. She described how her team addressed these concerns by conducting community seminars that explained mRNA vaccine technology in simple terms, emphasizing transparency. These communication efforts helped improve public trust, leading to a vaccination uptake among adolescents in her region that exceeded 70% by early 2022. Vaccination also brought emotional relief to families, especially those with vulnerable members, as it allowed for the restoration of intergenerational contact."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Schneider discussed the impact of vaccination on reducing severe respiratory cases and the subsequent decline in the severity of lung disease among hospitalized patients. He noted that as vaccine uptake increased, fewer patients required extended ventilation, allowing resources to be redirected to other pulmonary emergencies. However, there was no mention of vaccine hesitancy, the spread of misinformation, or specific communication efforts or vaccination drives aimed at improving public trust in the interview."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Meier discussed vaccine hesitancy and the spread of misinformation, noting that while Germany's vaccination campaign started strong with high uptake among healthcare workers and the elderly, resistance grew as the rollout expanded. He described how misinformation spread rapidly, particularly in certain regions, leading to some patients remaining unvaccinated and even dying while still believing COVID was exaggerated. Dr. Meier emphasized that vaccine hesitancy was rooted not just in ignorance but in mistrust, amplified by online echo chambers. He also mentioned that Germany's data transparency helped prove vaccine effectiveness, as hospitalization rates dropped sharply among the vaccinated. However, there is no mention of specific communication efforts or vaccination drives that improved public trust beyond the use of transparent data."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Kavita Joshi discussed vaccine hesitancy, particularly in rural areas, noting that it was significant at the start of India's vaccination drive. To address this, field teams engaged community influencers such as teachers, priests, and self-help groups to spread awareness. Communication efforts were localized using local languages and visual aids rather than English press releases, which led to a significant increase in vaccine uptake. By late 2021, most districts had achieved over 80% adult coverage, highlighting the effectiveness of these targeted communication strategies in building public trust and improving vaccination rates."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Roberts discussed both vaccine hesitancy and the spread of misinformation during the pandemic. She noted that misinformation, such as myths about masks and conspiracy theories about vaccines, spread rapidly, even among educated patients. To address this, her team launched community webinars, collaborated with local influencers, and trained clinicians in compassionate communication to correct misinformation empathetically. Regarding vaccination, Dr. Roberts described initial hesitancy among healthcare workers, which was addressed through transparent town halls with experts to answer questions about side effects and safety. These efforts led to over 95% of staff receiving their first dose within a month. For the public, the hospital partnered with community organizations and local media to run mobile clinics and information drives, ensuring equitable access and building public trust through both online and offline registration options."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Thompson discussed both vaccine hesitancy and the spread of misinformation in his community. He noted that while initial vaccine uptake among older populations was good, there was significant hesitancy among working-age adults and certain cultural groups. To address this, the hospital organized mobile vaccination clinics at churches, community centers, and local fairs to make vaccines more accessible. Building trust was a key strategy, involving local family physicians, clergy, and community leaders to communicate the benefits of vaccination. Despite these efforts, misinformation and political polarization continued to impede full vaccine uptake."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "The doctor did not specifically discuss vaccine hesitancy or the spread of misinformation related to vaccines. While he did mention the importance of communication in managing misinformation and fear during the pandemic, there was no direct reference to vaccination drives, efforts to improve public trust in vaccines, or strategies to address vaccine hesitancy. The focus was more on treatment protocols, resource allocation, collaboration, and the emotional impact of the pandemic on healthcare workers and patients."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Johnson discussed both vaccine hesitancy and the spread of misinformation. She described how addressing vaccine hesitancy required tailored conversations, listening to concerns, correcting misinformation, and using trusted community messengers. Efforts to improve public trust included deploying bilingual staff, collaborating with faith leaders, providing transparent information about side effects and benefits, and engaging in proactive outreach through social media, local radio, translated materials, and one-on-one discussions. These communication strategies, along with mass vaccination clinics and mobile units for homebound patients, were mentioned as ways to increase vaccine uptake and build trust within the community."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Priya Sharma discussed both vaccine hesitancy and the spread of misinformation during the COVID-19 pandemic. She noted that misinformation, often spread through social media and WhatsApp forwards, led families to believe in unproven treatments and contributed to panic and resource hoarding. To counter this, her team engaged in patient counseling and launched public videos and live Q&A sessions via hospital social media to address rumors and provide accurate information. Regarding vaccination, Dr. Sharma described initial public skepticism and slow vaccine uptake, but highlighted that communication efforts and on-site vaccination camps, especially in rural areas, helped improve public trust and increase vaccination rates. She emphasized the importance of clear messaging and equitable access in building trust and turning the tide of the pandemic."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Miller discussed vaccine hesitancy, particularly among certain communities, during the hospital's vaccination rollout. To address this, the hospital collaborated with community leaders and public housing groups to set up mobile clinics and multilingual education campaigns, emphasizing that equitable access to vaccines was a core mission. These targeted communication and outreach efforts were designed to improve public trust and ensure broad vaccine uptake. Additionally, Dr. Miller highlighted the importance of transparency and honest communication in building and maintaining public trust in healthcare systems, especially during crises."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Neha Reddy discussed both vaccine hesitancy and the spread of misinformation during the pandemic. She described initial skepticism about vaccines among both patients and healthcare workers, driven by myths about infertility, rapid vaccine development, and side effects. To address this, her team organized town halls, shared transparent data on vaccine safety, and led by example to build trust. For patients, they created a multilingual Q&A series online and collaborated with local community leaders, which gradually improved vaccine acceptance. Dr. Reddy also highlighted the significant impact of misinformation spread via social media, noting that patients often requested disproven treatments and delayed seeking care due to false information. She emphasized the importance of proactive public health communication to counteract misinformation and build public trust in vaccination efforts."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Fischer discussed both vaccine hesitancy and the spread of misinformation. He recounted an incident involving a man in his 40s who refused vaccination, later arriving at the hospital in critical condition and expressing regret for not getting vaccinated. Dr. Fischer noted that misinformation was rampant during the pandemic. Regarding vaccination drives, he mentioned that part of the emergency room was converted into a vaccination station for walk-ins, which brought hope to both staff and patients. While he did not detail specific communication efforts to improve public trust, he did highlight the impact of public gestures of support, such as thank-you notes and hand-knitted masks, which helped boost morale among healthcare workers."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Kumar discussed both vaccine hesitancy and the spread of misinformation during the pandemic. He noted that initially, there was hesitancy among healthcare workers regarding the COVID-19 vaccines due to concerns about side effects and the speed of development. However, as staff observed their colleagues tolerating the vaccine well, uptake increased rapidly, and within a month, over 95% of the staff were vaccinated. For the public, mass vaccination drives were organized in collaboration with local panchayats and NGOs, including converting college grounds into vaccination mega-camps and assisting elderly citizens with registration. Dr. Kumar also highlighted the challenge of misinformation, mentioning that families often brought prescriptions from social media and had misconceptions about treatments, which required significant counseling efforts. The state's centralized drug distribution and consistent public messaging helped reduce chaos and improve public trust."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anna Weber discussed both vaccine hesitancy and the spread of misinformation during the COVID-19 pandemic. She noted that her hospital faced resistance from a small percentage of staff who initially declined vaccination. To address this, they organized open forums, invited virologists to explain safety data, and encouraged dialogue, which eventually led to over 95% of staff being vaccinated. Dr. Weber also described the challenge of disinformation, mentioning false claims about masks and vaccines, and her efforts to counter these through community webinars explaining basic immunology. She emphasized that building public trust required transparency, clear communication, and empathy, and that scientists became trusted public figures by explaining uncertainty calmly and factually."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Anjali Singh discussed both vaccine hesitancy and the spread of misinformation during the pandemic. She noted that early on, rumors circulated that children could not catch COVID-19, leading some parents to ignore mild symptoms. Later, social media fueled panic with stories about vaccine-related infertility, growth problems, and conspiracy theories. To address these issues and improve public trust, Dr. Singh and her team organized community awareness camps, using pediatricians as trusted messengers. They communicated in local languages through radio and WhatsApp groups, focusing on empathetic explanations rather than arguments. Additionally, when vaccines were approved for adolescents, school-based vaccination drives were organized, and efforts were made to make the process child-friendly, such as using colorful posters, music, and doctors dressed in cartoon scrubs. These initiatives helped to build trust and encourage vaccination among children and their families."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Olivia Davis discussed vaccine hesitancy and the spread of misinformation, noting that blanket messaging was ineffective and that people had legitimate concerns. She described efforts to address hesitancy by training community ambassadors such as pastors, teachers, and local business owners to share their personal vaccination experiences and answer questions. The department also partnered with social scientists to understand the drivers of hesitancy, including distrust, misinformation, and historical trauma, and to design emotionally resonant counter-narratives. In some rural areas, trusted local figures like pharmacists and veterinarians became key messengers. Additionally, vaccination drives were tailored to improve public trust and access, with mobile units and clinics set up in churches, barbershops, and schools, and data transparency used to engage local leaders in addressing gaps in vaccine coverage."
  },
  {
    "query": "Vaccination and Public Trust: Did the doctor discuss vaccine hesitancy or the spread of misinformation? Were vaccination drives or communication efforts that improved public trust mentioned?",
    "filename": "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
    "response": "Dr. Vogel discussed the challenges posed by misinformation during the pandemic, describing it as an \"infodemic\" with an overabundance of false or distorted information. He noted that epidemiologists became targets of online abuse and that initial efforts to counter misinformation with more data and charts were ineffective, as emotion often outweighed logic. This realization led to collaboration with psychologists and communication experts, shifting the focus to narrative-driven communication, such as the impactful phrase \"Flattening the curve.\" Regarding vaccination, Dr. Vogel highlighted the critical role of vaccination campaigns in changing the course of the pandemic, noting that once vaccine coverage reached 60%, hospitalizations decoupled from case numbers. He also mentioned the challenges in public communication, particularly in explaining that vaccines prevent severe disease rather than infection, which led to some confusion. Overall, the interview emphasizes the importance of trust, empathy, and effective communication in public health efforts, including vaccination drives."
  }
]

    notes = [{k: v for k, v in note.items() if k != 'pointers'} for note in notes]

    # Other parameters
    target_document_type = 'doc' # 'html'
    target_document_length = '200 words' # 'XX slides' or 'XX words'
    target_document_brief = (
        """
        Produce a concise handbook summarizing the most effective strategies and practices identified by doctors across the three countries. Include hospital management, staff support, technology adoption, communication approaches, and equity-focused interventions. Organize by actionable guidelines
        """
    )

    writer.create_draft(target_document_type,target_document_length,target_document_brief,notes)
