"""
Seeds sample high-quality lesson packages into data/lessons/
so that new users can immediately explore LessonForge's full functionality.
"""
from datetime import datetime
from pathlib import Path

from core.models import (
    BookSource,
    LessonMetadata,
    LessonPackage,
    LessonVersion,
    QCAccuracyFinding,
    QCFactualReport,
    QCPedagogicalRecommendation,
    QCPedagogicalReport,
    ResearchDossier,
    VideoSource,
    WebSource,
)
from core.storage import save_new_lesson, save_lesson_version


def seed_lessons():
    print("🌱 Seeding sample lessons for LessonForge...")

    # =========================================================================
    # Sample Lesson 1: Biology / Science
    # =========================================================================
    lesson_id_1 = "photosynthesis-light-reactions-sample"
    title_1 = "Photosynthesis: Light-Dependent Reactions & ATP Synthesis"
    objective_1 = (
        "SWBAT trace the flow of excited electrons from Photosystem II to Photosystem I, "
        "explain the role of photolysis in replenishing electrons and generating oxygen, "
        "and describe how the resulting proton gradient across the thylakoid membrane drives ATP synthase."
    )

    dossier_1 = ResearchDossier(
        query="Photosynthesis light dependent reactions",
        retrieved_at=datetime.now().isoformat(),
        web_sources=[
            WebSource(
                id="web-1",
                title="The Light-Dependent Reactions of Photosynthesis - OpenStax Biology",
                url="https://openstax.org/books/biology-2e/pages/8-2-the-light-dependent-reactions-of-photosynthesis",
                snippet="Photons strike chlorophyll pigments in Photosystem II, exciting electrons that are passed through an electron transport chain to Photosystem I, generating a proton gradient across the thylakoid lumen.",
                content="Photosynthesis begins when light energy is absorbed by pigment-protein complexes called photosystems embedded in the thylakoid membrane of chloroplasts. Photosystem II (PSII) absorbs light at 680 nm. The excited reaction center chlorophyll, P680, transfers high-energy electrons to pheophytin and plastoquinone. Water splitting (photolysis) by the oxygen-evolving complex replaces these electrons, releasing molecular oxygen and protons into the lumen.",
                engine="DuckDuckGo",
            ),
            WebSource(
                id="web-2",
                title="Photosynthesis: The Light Reactions - Nature Scitable",
                url="https://www.nature.com/scitable/topicpage/photosynthetic-cells-14025371/",
                snippet="Chemiosmotic ATP synthesis in chloroplasts relies on the electrochemical proton motive force across the thylakoid membrane driven by the cytochrome b6f complex.",
                content="As electrons flow from PSII to PSI through plastoquinone, the cytochrome b6f complex, and plastocyanin, protons are actively translocated from the stroma into the thylakoid lumen. This electrochemical potential powers ATP synthase via chemiosmosis.",
                engine="DuckDuckGo",
            )
        ],
        book_sources=[
            BookSource(
                id="book-1",
                title="Molecular Mechanisms of Photosynthesis",
                authors=["Robert E. Blankenship"],
                publisher="Wiley-Blackwell",
                year="2021",
                description="Comprehensive graduate-level analysis of solar energy capture, light absorption by antenna complexes, and electron transfer pathways in oxygenic photosystems.",
                info_link="https://www.google.com/books/edition/Molecular_Mechanisms_of_Photosynthesis/sample",
                isbn="978-1119370147",
            ),
            BookSource(
                id="book-2",
                title="Campbell Biology (12th Edition)",
                authors=["Lisa A. Urry", "Michael L. Cain", "Steven A. Wasserman"],
                publisher="Pearson",
                year="2020",
                description="Standard biological text explaining cellular energetics, chloroplast structure, linear electron flow, cyclic photophosphorylation, and Calvin cycle coupling.",
                info_link="https://openlibrary.org/works/OL19918231W",
                isbn="978-0135188743",
            )
        ],
        video_sources=[
            VideoSource(
                id="video-1",
                title="Photosynthesis: Light Reactions and Photophosphorylation",
                channel="Amoeba Sisters",
                video_id="CMiPYHNNg28",
                url="https://www.youtube.com/watch?v=CMiPYHNNg28",
                description="Visual step-by-step walkthrough of thylakoid membrane structures, electron transport chains, and proton gradient generation.",
                duration="08:45",
                transcript_available=True,
                transcript_excerpt="Light hits photosystem two, which excites electrons that travel down the chain. Water gets split to replace those electrons, which is why plants release oxygen!",
            )
        ],
        raw_context="Grounded synthesis of OpenStax Biology and Blankenship (2021)."
    )

    content_1 = """# Photosynthesis: Light-Dependent Reactions & ATP Synthesis

## 1. Lesson Metadata & Learning Objectives
- **Target Grade Level:** Grade 9-10 (Early High School Biology)
- **Subject / Topic Area:** Biology & Life Sciences (Cellular Energetics)
- **Duration:** 45 Minutes
- **Measurable Learning Objective (SWBAT):** Students Will Be Able To (SWBAT) trace the flow of excited electrons from Photosystem II through the electron transport chain to Photosystem I, explain the essential role of photolysis in releasing O₂ [Web 1], and describe how the resulting proton gradient across the thylakoid membrane drives ATP synthase [Book 1].
- **Key Essential Question:** How do plant cells physically transform electromagnetic radiation from sunlight into stable chemical bonds?

---

## 2. Classroom Materials & Setup
- Color-coded laminated membrane cards (representing PSII, PSI, Cytochrome b6f, and ATP Synthase)
- Ping pong balls (labeled $e^-$ for electrons and $H^+$ for protons)
- Projector for Amoeba Sisters visual animation [Video 1]
- Exit ticket half-sheets

---

## 3. 45-Minute Structured Agenda Breakdown

### 00:00 - 05:00 | The Hook & Inquiry Ignition (5 Mins)
- **Teacher Action:** Turn off classroom lights. Display an airtight sealed terrarium with healthy green plants.
- **Teacher Script:** *"For centuries, people believed plants literally ate dirt to grow larger. In 1779, Jan Ingenhousz discovered that plants submerged in water only bubble gas when placed in direct sunlight. Where is that gas coming from, and where does the plant get its power?"*
- **Student Action:** 90-second silent written hypothesis on their warm-up cards, followed by quick 90-second Turn-and-Talk with table partners.

### 05:00 - 20:00 | Direct Instruction & Conceptual Architecture (15 Mins)
- **Step 1: Photon Capture & Photolysis [Web 1]:** Explain how P680 chlorophyll absorbs light energy, elevating electrons to a higher energy level. Explain water photolysis: $2\text{H}_2\text{O} \rightarrow 4\text{H}^+ + 4e^- + \text{O}_2$. Emphasize that the oxygen we breathe is merely a byproduct of plants refilling empty electron slots!
- **Step 2: Electron Transport & Proton Pumping [Web 2, Book 1]:** Trace the electron pathway through Plastoquinone to the Cytochrome b6f complex. Explain that electron transfer powers the active pumping of $H^+$ from the stroma into the thylakoid lumen, establishing a steep concentration gradient.
- **Step 3: Chemiosmosis & ATP Synthase [Book 2]:** Explain how protons escape the lumen through ATP Synthase, rotating the catalytic headpiece to phosphorylate ADP into ATP.
- **Anticipated Misconceptions:** Students commonly assume that the oxygen released by plants comes from carbon dioxide ($CO_2$). Explicitly highlight that isotopic oxygen tracing proves all emitted $O_2$ originates from split water molecules [Book 1].
- **Check for Understanding (CFU):** *"Thumb Check: If a herbicide disables plastoquinone, does oxygen production stop immediately, or does ATP synthesis stop first?"* (Cold call 2 students).

### 20:00 - 35:00 | Guided Practice: The Kinesthetic Electron Relay (15 Mins)
- **Activity Design:** Students work in teams of 4. Each student represents a membrane station:
  1. Student A: Photosystem II (absorbs photon card, splits water ball, passes electron)
  2. Student B: Cytochrome b6f (moves proton balls from 'Stroma' side to 'Lumen' bucket)
  3. Student C: Photosystem I (re-energizes electron with second photon card, forms NADPH)
  4. Student D: ATP Synthase (uses accumulated lumen proton balls to generate ATP token)
- **Teacher Role:** Circulate with a formative checklist, probing teams: *"Show me where the proton gradient is highest right now."*

### 35:00 - 40:00 | Independent Practice & Synthesis (5 Mins)
- **Student Work:** Each student independently completes a 3-box diagram labeling:
  1. The location of photolysis.
  2. The direction of proton pumping.
  3. The chemical outputs exiting into the stroma ($ATP$ and $NADPH$).

### 40:00 - 45:00 | Closure, Exit Ticket & Formative Assessment (5 Mins)
- **Exit Ticket Questions:**
  1. *What is the specific source of electrons that replace those excited and lost by Photosystem II?*
  2. *Explain why uncoupling the thylakoid membrane (poking microscopic holes in it) stops ATP production even if sunlight continues to strike the leaf.*
- **Collection:** Collected at the classroom door as the bell rings for immediate scoring.

---

## 4. Inclusivity & Differentiation
- **For Struggling Learners:** Visual flowcharts with directional arrows and color-coded chemical labels ($e^-$ in yellow, $H^+$ in blue).
- **For Advanced Learners:** Extension prompt exploring cyclic photophosphorylation: why would a chloroplast cycle electrons around PSI without making NADPH?
- **Multilingual Learners:** Dual-language vocabulary cards pairing English and Spanish terms (*Thylakoid / Tilacoide*, *Gradient / Gradiente*).

---

## 5. Verified Source Citations & References
- `[Web 1]` OpenStax Biology 2e: Section 8.2 Light-Dependent Reactions (https://openstax.org/books/biology-2e/pages/8-2-the-light-dependent-reactions-of-photosynthesis)
- `[Web 2]` Nature Scitable: Photosynthetic Cells and Cellular Energetics (https://www.nature.com/scitable/topicpage/photosynthetic-cells-14025371/)
- `[Book 1]` Blankenship, R. E. (2021). *Molecular Mechanisms of Photosynthesis*. Wiley-Blackwell.
- `[Book 2]` Urry, L. A., et al. (2020). *Campbell Biology (12th Ed.)*. Pearson.
- `[Video 1]` Amoeba Sisters. *Photosynthesis: Light Reactions and Photophosphorylation*. (https://www.youtube.com/watch?v=CMiPYHNNg28)
"""

    qc_fact_1 = QCFactualReport(
        overall_score=98,
        status="PASS",
        summary="Exceptional factual grounding. All biochemical claims, membrane locations, and equations are directly substantiated by OpenStax and Blankenship (2021).",
        findings=[
            QCAccuracyFinding(
                claim="Water photolysis replaces excited electrons at PSII and releases O2.",
                citation_ref="[Web 1]",
                status="VERIFIED",
                explanation="Accurately reflects the standard biochemical water splitting mechanism.",
                suggestion="No change needed.",
            ),
            QCAccuracyFinding(
                claim="Protons are actively translocated into the thylakoid lumen by Cytochrome b6f.",
                citation_ref="[Web 2, Book 1]",
                status="VERIFIED",
                explanation="Directly corroborated by peer-reviewed biophysical literature.",
                suggestion="No change needed.",
            ),
            QCAccuracyFinding(
                claim="Isotopic oxygen tracing confirms O2 derives from water rather than CO2.",
                citation_ref="[Book 1]",
                status="VERIFIED",
                explanation="Accurate historical confirmation from Ruben, Randall, Kamen, and Blankenship.",
                suggestion="No change needed.",
            )
        ],
        verified_count=3,
        unsupported_count=0,
        contradicted_count=0,
    )

    qc_ped_1 = QCPedagogicalReport(
        overall_score=95,
        status="EXCELLENT",
        alignment_score=98,
        pacing_score=94,
        engagement_score=96,
        assessment_score=94,
        strengths=[
            "Strict 45-minute bell-to-bell allocation with distinct 5-min increments.",
            "Kinesthetic electron relay activity provides an active mental model of abstract molecular processes.",
            "Formative exit ticket questions directly assess causal reasoning and Bloom's synthesis.",
        ],
        areas_for_growth=[
            "Ensure the kinesthetic relay setup takes under 2 minutes so practice time is not compromised.",
        ],
        recommendations=[
            QCPedagogicalRecommendation(
                id="rec-bio-1",
                area="Pacing & Timing",
                current_state="Materials transition to guided practice relies on verbal distribution.",
                recommendation="Pre-set card packets on student desks prior to the start of class.",
                concrete_action="Add teacher setup note: 'Place kinesthetic relay packets on desks before the period begins.'",
                severity="LOW",
                applied=True,
            )
        ]
    )

    pkg_1 = LessonPackage(
        metadata=LessonMetadata(
            id=lesson_id_1,
            title=title_1,
            objective=objective_1,
            grade_level="Grade 9-10 (Early High School)",
            subject="Biology & Life Sciences",
            duration_minutes=45,
            current_version=2,
            total_versions=2,
        ),
        markdown_content=content_1,
        research_dossier=dossier_1,
        qc_factual=qc_fact_1,
        qc_pedagogical=qc_ped_1,
        versions=[
            LessonVersion(version_number=1, note="Initial AI synthesis", content=content_1),
            LessonVersion(version_number=2, note="Teacher refinement & transition optimizations", content=content_1),
        ]
    )
    save_new_lesson(pkg_1)
    save_lesson_version(lesson_id_1, content_1, note="Teacher refinement & transition optimizations")
    print(f"  ✅ Seeded Lesson 1: {title_1}")

    # =========================================================================
    # Sample Lesson 2: Computer Science / Mathematics
    # =========================================================================
    lesson_id_2 = "sorting-algorithms-big-o-sample"
    title_2 = "Algorithmic Efficiency: Comparing Bubble Sort vs Merge Sort"
    objective_2 = (
        "SWBAT compare the time complexity of Bubble Sort O(n^2) and Merge Sort O(n log n), "
        "demonstrate the divide-and-conquer strategy on an 8-element list, "
        "and determine which algorithm is suitable for large-scale datasets."
    )

    dossier_2 = ResearchDossier(
        query="Sorting algorithms merge sort bubble sort big o complexity",
        retrieved_at=datetime.now().isoformat(),
        web_sources=[
            WebSource(
                id="web-1",
                title="Sorting Algorithms Analysis - GeeksforGeeks",
                url="https://www.geeksforgeeks.org/sorting-algorithms/",
                snippet="Comparison of elementary vs divide-and-conquer sorting algorithms, detailing worst-case, average-case, and space complexities.",
                content="Bubble Sort repeatedly steps through the list, compares adjacent elements and swaps them if they are in the wrong order, resulting in an O(n^2) time complexity. Merge Sort is a divide-and-conquer algorithm that divides the array into halves, recursively sorts them, and merges the sorted halves in O(n log n) time.",
                engine="DuckDuckGo",
            )
        ],
        book_sources=[
            BookSource(
                id="book-1",
                title="Introduction to Algorithms (CLRS, 4th Edition)",
                authors=["Thomas H. Cormen", "Charles E. Leiserson", "Ronald L. Rivest", "Clifford Stein"],
                publisher="MIT Press",
                year="2022",
                description="The definitive computer science reference covering asymptotic notation, recurrence trees, and divide-and-conquer sorting paradigms.",
                info_link="https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/",
                isbn="978-0262046305",
            )
        ],
        video_sources=[
            VideoSource(
                id="video-1",
                title="Merge Sort in 3 Minutes - Quick and Intuitive",
                channel="Computerphile",
                video_id="alJswNJ4P3U",
                url="https://www.youtube.com/watch?v=alJswNJ4P3U",
                description="Visual step-by-step split and merge animation demonstrating recursive tree partitioning.",
                duration="03:45",
                transcript_available=True,
                transcript_excerpt="We split the list down until we have single items. Single items are already sorted! Then we merge pairs back together in order.",
            )
        ],
        raw_context="Grounded synthesis of CLRS (2022) and GeeksforGeeks algorithmic analysis."
    )

    content_2 = """# Algorithmic Efficiency: Comparing Bubble Sort vs Merge Sort

## 1. Lesson Metadata & Learning Objectives
- **Target Grade Level:** Grade 11-12 (Advanced Placement / Introductory CS)
- **Subject / Topic Area:** Computer Science & Mathematics
- **Duration:** 45 Minutes
- **Measurable Learning Objective (SWBAT):** SWBAT trace the execution steps of Bubble Sort and Merge Sort on an 8-element array, explain why divide-and-conquer achieves $O(n \log n)$ time complexity [Book 1], and justify the selection of sorting algorithms based on dataset size and memory constraints [Web 1].
- **Key Essential Question:** When an algorithm works correctly, why does its growth rate matter so critically as data scales to billions of items?

---

## 2. Classroom Materials & Setup
- Decks of numbered playing cards (Ace through 8) for student pairs
- Stopwatch / phone timer for the physical card-sorting benchmark
- Whiteboard markers (two colors: blue for splitting, red for merging)

---

## 3. 45-Minute Structured Agenda Breakdown

### 00:00 - 05:00 | The Hook: The Human Search Race (5 Mins)
- **Teacher Action:** Invite two volunteers to the front of the room. Hand Volunteer A a shuffled deck of 100 business cards with names, and hand Volunteer B an alphabetized rolodex. Ask both to locate "Marcus Vance".
- **Teacher Script:** *"Volunteer B found Marcus in 2 seconds; Volunteer A is still flipping. How we organize data determines whether an application runs in milliseconds or freezes for hours. Today, we conquer sorting algorithms."*
- **Student Action:** Quick paired discussion: How would you systematically sort 8 unsorted numbers using only basic comparisons?

### 05:00 - 20:00 | Direct Instruction: $O(n^2)$ vs. Divide-and-Conquer (15 Mins)
- **Bubble Sort Mechanics [Web 1]:** Show adjacent comparisons and swaps. Derive total comparisons: $(n-1) + (n-2) + \dots + 1 = \frac{n(n-1)}{2} \approx O(n^2)$. Point out that for $10^6$ elements, $n^2 = 10^{12}$ operations (roughly 15 minutes of compute).
- **Merge Sort Mechanics [Book 1]:** Introduce Divide-and-Conquer:
  1. *Divide:* Recursively split array into halves until subarrays have size 1.
  2. *Conquer:* Base cases of size 1 are trivially sorted.
  3. *Combine (Merge):* Merge two sorted subarrays using two pointers in $O(n)$ time.
- **The Tree of Recursion:** Draw the recursion tree. Height is $\log_2 n$. Work per level is $c \cdot n$. Total time: $O(n \log n)$. For $10^6$ items, $n \log_2 n \approx 2 \times 10^7$ operations (less than 0.05 seconds!).
- **Anticipated Misconceptions:** Students often believe Merge Sort is always superior; explicitly note its auxiliary space requirement $O(n)$ compared to Bubble Sort's in-place $O(1)$ space.

### 20:00 - 35:00 | Guided Practice: Card-Sorting Benchmark Relay (15 Mins)
- **Activity Design:** Working in pairs with cards Ace through 8:
  - Round 1: Partner 1 executes manual Bubble Sort while Partner 2 counts total comparisons and swaps on a tally chart.
  - Round 2: Partner 2 executes Merge Sort (splitting into single cards, then executing 2-pointer zip merges) while Partner 1 tallies comparisons.
- **Data Synthesis:** Teams post their operation counts on the board table.

### 35:00 - 40:00 | Independent Practice & Scenario Selection (5 Mins)
- **Student Work:** Students independently evaluate 2 engineering scenarios:
  1. An embedded pacemaker with 16 bytes of RAM sorting 6 sensor readings (Choose algorithm and justify based on space constraints).
  2. A streaming service sorting 40 million song titles alphabetically (Choose algorithm and justify based on asymptotic scaling).

### 40:00 - 45:00 | Closure, Exit Ticket & Formative Assessment (5 Mins)
- **Exit Ticket Questions:**
  1. *If an algorithm takes 4 seconds to sort 1,000 items, how long will it take to sort 10,000 items if its complexity is $O(n^2)$?*
  2. *Why are single-element arrays considered already sorted in the divide-and-conquer base case?*
- **Collection:** Collected at the door as students exit.

---

## 4. Inclusivity & Differentiation
- **For Struggling Learners:** Visual tree diagram worksheets pre-drawn with empty boxes to guide the splitting and merging steps.
- **For Advanced Learners:** Challenge question asking students to analyze the Best-Case time complexity of optimized Bubble Sort with an early-exit `swapped` boolean flag.

---

## 5. Verified Source Citations & References
- `[Web 1]` GeeksforGeeks: Comprehensive Sorting Algorithms Analysis (https://www.geeksforgeeks.org/sorting-algorithms/)
- `[Book 1]` Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms (4th Ed.)*. MIT Press.
- `[Video 1]` Computerphile: Merge Sort in 3 Minutes (https://www.youtube.com/watch?v=alJswNJ4P3U)
"""

    qc_fact_2 = QCFactualReport(
        overall_score=100,
        status="PASS",
        summary="Flawless algorithmic complexity analysis. Recurrence relations, space tradeoffs, and asymptotic proofs match CLRS (2022).",
        findings=[
            QCAccuracyFinding(
                claim="Merge sort divides an array into halves and achieves O(n log n) time.",
                citation_ref="[Book 1]",
                status="VERIFIED",
                explanation="Matches Theorem 2.1 in Cormen et al. (CLRS).",
                suggestion="No change needed.",
            ),
            QCAccuracyFinding(
                claim="Bubble sort worst-case time is O(n^2) with O(1) auxiliary space.",
                citation_ref="[Web 1]",
                status="VERIFIED",
                explanation="Standard complexity established in computer science literature.",
                suggestion="No change needed.",
            )
        ],
        verified_count=2,
        unsupported_count=0,
        contradicted_count=0,
    )

    qc_ped_2 = QCPedagogicalReport(
        overall_score=94,
        status="EXCELLENT",
        alignment_score=96,
        pacing_score=92,
        engagement_score=95,
        assessment_score=92,
        strengths=[
            "Tangible hands-on card manipulation demystifies theoretical Big-O notation.",
            "Strong real-world hook comparing sorted vs unsorted retrieval time.",
            "Independent practice scenarios challenge students with real engineering tradeoffs (RAM vs CPU).",
        ],
        areas_for_growth=[
            "Monitor card-counting tallies closely to ensure students don't skip comparison counts.",
        ],
        recommendations=[]
    )

    pkg_2 = LessonPackage(
        metadata=LessonMetadata(
            id=lesson_id_2,
            title=title_2,
            objective=objective_2,
            grade_level="Grade 11-12 (Advanced Placement)",
            subject="Computer Science & Mathematics",
            duration_minutes=45,
            current_version=1,
            total_versions=1,
        ),
        markdown_content=content_2,
        research_dossier=dossier_2,
        qc_factual=qc_fact_2,
        qc_pedagogical=qc_ped_2,
        versions=[
            LessonVersion(version_number=1, note="Initial publication", content=content_2),
        ]
    )
    save_new_lesson(pkg_2)
    print(f"  ✅ Seeded Lesson 2: {title_2}")

    print("🎉 Seeding complete! 2 high-quality sample lessons are now available in LessonForge.")


if __name__ == "__main__":
    seed_lessons()
