"""
Prompt profiles implementing the Strategy pattern for educational level adaptation.
Each educational stage configures tailored pedagogy:
  - Audience comprehension expectations
  - Vocabulary and sentence length constraints
  - Difficulty interpretation (what easy/medium/hard means at that stage)
  - Distractor design principles (obvious vs common misconception vs subtle methodological flaw)
  - Default Bloom's Taxonomy spectrum
  - Stage-authentic few-shot exemplars
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Final, Mapping, Sequence, Tuple
from types import MappingProxyType
from .levels import Stage, EducationLevel


@dataclass(frozen=True, slots=True)
class PromptProfile:
    stage: Stage
    audience_description: str
    language_and_reading_rules: str
    difficulty_guide: Mapping[str, str]
    distractor_guidelines: str
    default_blooms: Tuple[str, ...]
    few_shot_examples: Tuple[dict, ...]

    def render_instruction_block(self, level: EducationLevel, selected_diffs: Sequence[str]) -> str:
        """Render the pedagogical guideline block to inject into LLM prompts."""
        diff_lines = []
        for d in selected_diffs:
            d_norm = d.lower().strip()
            explanation = self.difficulty_guide.get(
                d_norm,
                f"{d.capitalize()} level appropriate for {level.label}."
            )
            diff_lines.append(f"  * {d.upper()}: {explanation}")

        diff_block = "\n".join(diff_lines) if diff_lines else "  * Standard stage difficulty."
        blooms_str = ", ".join(self.default_blooms)

        return f"""=== TARGET PEDAGOGICAL PROFILE: {level.label.upper()} (STAGE: {self.stage.value.upper()}) ===
1. AUDIENCE & COGNITIVE EXPECTATION:
- Target Learner: {self.audience_description}
- Age Group: {f'{level.typical_age[0]}-{level.typical_age[1]} years old' if level.typical_age else 'Adult / Mature Learner'}
- Primary Bloom's Domains: {blooms_str}

2. LANGUAGE & SYNTAX CONSTRAINTS:
{self.language_and_reading_rules}

3. DIFFICULTY CALIBRATION FOR THIS STAGE:
{diff_block}

4. DISTRACTOR (WRONG OPTION) DESIGN:
{self.distractor_guidelines}
- Maximum options per question: {level.max_choices}
"""


# 1. Early Years (Kindergarten / Nursery)
_EARLY_YEARS_PROFILE = PromptProfile(
    stage=Stage.EARLY_YEARS,
    audience_description="Young learners (ages 4-6) acquiring foundational language and observation skills.",
    language_and_reading_rules="""- Use extremely simple, clear words (e.g., 'sun', 'water', 'plant', 'big', 'small').
- Sentence length must NOT exceed 10 words.
- Absolutely NO double negatives, passive voice, or abstract metaphors.
- Frame questions around tangible, real-world objects and sensory observations.""",
    difficulty_guide={
        "easy": "Direct identification of common objects, colors, basic shapes, or numbers 1-10.",
        "medium": "Simple categorization (e.g., animals that fly vs walk) or two-step daily routines.",
        "hard": "Simple cause-and-effect (e.g., what happens when rain falls on plants) using simple words.",
    },
    distractor_guidelines="""- Keep wrong options friendly, familiar, and clearly distinct.
- Avoid trick questions or confusing linguistic traps.
- Exactly 3 options per question.""",
    default_blooms=("Remember", "Understand"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "Which of these animals can fly in the sky?",
            "choices": ["Bird", "Fish", "Dog"],
            "answer": "A",
            "rationale": "Birds have wings that help them fly in the air.",
            "blooms_level": "Remember",
            "difficulty": "easy"
        },
        {
            "qtype": "true_false",
            "question": "Plants need water and sunlight to grow.",
            "choices": ["True", "False"],
            "answer": "True",
            "rationale": "Water and sunshine give plants energy to grow big and green.",
            "blooms_level": "Understand",
            "difficulty": "easy"
        }
    )
)

# 2. Primary / Elementary (Class 1 to 6)
_PRIMARY_PROFILE = PromptProfile(
    stage=Stage.PRIMARY,
    audience_description="Primary school pupils (ages 6-12) developing reading comprehension, basic mathematics, and fundamental science.",
    language_and_reading_rules="""- Keep sentences concise (10-18 words max).
- Use vocabulary suitable for primary school students (grade 1-6).
- Avoid convoluted clauses, jargon, or confusing phrasing.
- Ensure scenarios are relatable to a child's everyday school or home life.""",
    difficulty_guide={
        "easy": "Direct factual recall and vocabulary identification directly visible in the text.",
        "medium": "Simple concept application, single-step math calculations, or primary text inferences.",
        "hard": "Two-step reasoning, comparing two entities, or explaining 'why' something happened.",
    },
    distractor_guidelines="""- Distractors should represent typical primary student misconceptions, common spelling/math calculation slips, or related but incorrect category members.
- Keep options parallel in grammatical structure and approximately equal in length.""",
    default_blooms=("Remember", "Understand", "Apply"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "What part of a plant takes in water from the soil?",
            "choices": ["Roots", "Leaves", "Flowers", "Stem"],
            "answer": "A",
            "rationale": "Roots grow underground to anchor the plant and absorb water and nutrients from the soil.",
            "blooms_level": "Remember",
            "difficulty": "easy"
        },
        {
            "qtype": "true_false",
            "question": "The moon produces its own light just like the sun.",
            "choices": ["True", "False"],
            "answer": "False",
            "rationale": "The moon does not produce its own light; it reflects light coming from the sun.",
            "blooms_level": "Understand",
            "difficulty": "medium"
        },
        {
            "qtype": "short_answer",
            "question": "Why do living things need food?",
            "choices": [],
            "answer": "Living things need food to get energy to grow, stay healthy, and move.",
            "rationale": "Pupils should mention providing energy, growth, or survival.",
            "blooms_level": "Understand",
            "difficulty": "easy"
        }
    )
)

# 3. Junior Secondary / Middle School (JHS 1-3 / Grade 7-9)
_JUNIOR_SEC_PROFILE = PromptProfile(
    stage=Stage.JUNIOR_SECONDARY,
    audience_description="Early adolescents (ages 12-15) transitioning to formal academic disciplines, basic scientific method, and intermediate algebra.",
    language_and_reading_rules="""- Use standard academic English with foundational subject terms (e.g., 'photosynthesis', 'ratio', 'democracy').
- Sentence structures can include compound-complex sentences with clear conjunctions.
- Avoid colloquialisms while avoiding overly dense graduate-level syntax.""",
    difficulty_guide={
        "easy": "Recall of established definitions, identifying key laws or historical dates.",
        "medium": "Applying formulas to standard problems, interpreting charts or short diagrams, explaining causes.",
        "hard": "Multi-step analytical reasoning, distinguishing correlation from causation, evaluating competing claims.",
    },
    distractor_guidelines="""- Distractors must address common conceptual misunderstandings (e.g., confusing mass with weight, or speed with velocity).
- Do not make wrong choices obviously absurd; all options must sound believable to a middle school student.""",
    default_blooms=("Remember", "Understand", "Apply", "Analyze"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "Which state of matter has a definite volume but takes the shape of its container?",
            "choices": ["Liquid", "Solid", "Gas", "Plasma"],
            "answer": "A",
            "rationale": "Liquids have fixed volume due to cohesive intermolecular forces, but flow freely to fit container shapes.",
            "blooms_level": "Understand",
            "difficulty": "easy"
        },
        {
            "qtype": "short_answer",
            "question": "Explain how an increase in temperature affects the rate of dissolving sugar in water.",
            "choices": [],
            "answer": "Higher temperatures increase the kinetic energy of water molecules, causing more frequent collisions and faster dissolving.",
            "rationale": "Full marks require connecting temperature to particle energy/movement and dissolution speed.",
            "blooms_level": "Apply",
            "difficulty": "medium"
        }
    )
)

# 4. Senior Secondary / High School (SHS 1-3 / Grade 10-12)
_SENIOR_SEC_PROFILE = PromptProfile(
    stage=Stage.SENIOR_SECONDARY,
    audience_description="High school students (ages 15-18) preparing for national and international board examinations (WASSCE, SAT, A-Levels, AP, IB).",
    language_and_reading_rules="""- Rigorous, formal exam-standard academic prose.
- Precise disciplinary terminology and symbolic notation where relevant.
- Questions should be self-contained, objective, and unambiguous.""",
    difficulty_guide={
        "easy": "Direct identification of core theoretical principles, key formulas, or standard nomenclature.",
        "medium": "Multi-step quantitative calculations, contextual passage interpretation, applied problem scenarios.",
        "hard": "Synthesis across two distinct concepts, experimental error analysis, or hypothesis critique.",
    },
    distractor_guidelines="""- Distractors must represent plausible pitfalls: sign errors, reciprocal calculations, partial answers, or classic textbook misconceptions.
- Distractors should be grammatically indistinguishable from the correct answer.""",
    default_blooms=("Understand", "Apply", "Analyze", "Evaluate"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "In cellular respiration, what is the net yield of ATP molecules generated per glucose molecule during glycolysis?",
            "choices": ["2 ATP", "4 ATP", "32 ATP", "36 ATP"],
            "answer": "A",
            "rationale": "Glycolysis consumes 2 ATP and produces 4 ATP, yielding a net gain of 2 ATP per glucose molecule.",
            "blooms_level": "Understand",
            "difficulty": "medium"
        },
        {
            "qtype": "true_false",
            "question": "Enzymes increase the rate of a chemical reaction by raising the reaction's activation energy barrier.",
            "choices": ["True", "False"],
            "answer": "False",
            "rationale": "Enzymes catalyze reactions by LOWERING the activation energy, enabling the reaction to proceed faster.",
            "blooms_level": "Analyze",
            "difficulty": "medium"
        }
    )
)

# 5. Diploma / TVET / Polytechnic (Applied & Technical Credentials)
_DIPLOMA_PROFILE = PromptProfile(
    stage=Stage.DIPLOMA,
    audience_description="Post-secondary students (ages 18-22+) pursuing vocational, polytechnic, technical college, or national diplomas (ND/HND/Associate) demanding applied technical competencies and real-world execution.",
    language_and_reading_rules="""- Applied technical and vocational terminology appropriate for polytechnic, laboratory, and field practice.
- Frame questions around real-world procedural scenarios, workshop operations, diagnostic troubleshooting, and industry specifications.
- Emphasize practical application, safety protocols, standard operating procedures, and technical problem-solving.""",
    difficulty_guide={
        "easy": "Standard operating procedures, tool and instrument identification, routine equipment safety, basic formula computation.",
        "medium": "Troubleshooting operational faults, practical system diagnostics, component sizing calculations, interpreting engineering/technical schematics.",
        "hard": "Multi-variable technical root-cause analysis, optimizing production/workshop workflows, addressing compliance and quality-assurance failures.",
    },
    distractor_guidelines="""- Distractors must represent plausible procedural shortcuts, common workshop/field miscalculations, or dangerous operational errors.
- Keep choices grammatically consistent and practically realistic.""",
    default_blooms=("Understand", "Apply", "Analyze"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "When diagnosing an industrial hydraulic circuit where the actuator moves sluggishly under load, which diagnostic measurement should the technician verify first?",
            "choices": [
                "System pressure at the relief valve under full operating load",
                "Total fluid volume in the unpressurized reservoir tank",
                "Ambient air temperature surrounding the return manifold",
                "Color and opacity of the exterior cylinder paint coating"
            ],
            "answer": "A",
            "rationale": "Sluggish actuator response under load typically indicates pressure loss or faulty relief valve setting, making load pressure verification the primary diagnostic step.",
            "blooms_level": "Apply",
            "difficulty": "medium"
        },
        {
            "qtype": "true_false",
            "question": "In electrical installations, a residual current device (RCD) is specifically designed to protect against sustained thermal overload from excessive current draw.",
            "choices": ["True", "False"],
            "answer": "False",
            "rationale": "RCDs detect residual earth leakage currents to prevent electric shock; circuit breakers (MCBs) protect against sustained thermal overload and short circuits.",
            "blooms_level": "Understand",
            "difficulty": "medium"
        }
    )
)

# 6. Undergraduate (Years 1 to 4 / Level 100-400)
_UNDERGRADUATE_PROFILE = PromptProfile(
    stage=Stage.UNDERGRADUATE,
    audience_description="University students (ages 18-22+) pursuing bachelor's degrees requiring domain models, research literature comprehension, and critical analysis.",
    language_and_reading_rules="""- Professional academic discourse with complete domain terminology.
- Frame questions using realistic case studies, clinical vignettes, business scenarios, or laboratory protocols.
- Avoid elementary definitions; test mechanisms, interactions, trade-offs, and boundary conditions.""",
    difficulty_guide={
        "easy": "Comprehension of major domain paradigms, canonical models, and standard operational definitions.",
        "medium": "Comparative evaluation of models, diagnosing failure modes in systems, applying theoretical frameworks to unseen scenarios.",
        "hard": "Evaluating conflicting experimental data, multi-variable trade-off analysis, or critiquing methodology.",
    },
    distractor_guidelines="""- Distractors must represent legitimate competing theories, valid concepts applied to the wrong condition, or mathematically consistent misapplications.
- Wrong choices should require genuine domain competence to eliminate.""",
    default_blooms=("Apply", "Analyze", "Evaluate", "Create"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "In distributed database systems, which property does the CAP theorem state must be sacrificed during a network partition if strong consistency is guaranteed?",
            "choices": ["Availability", "Atomicity", "Durability", "Linearizability"],
            "answer": "A",
            "rationale": "Under Brewer's CAP theorem, during a network partition (P), a distributed system can maintain Consistency (C) only by refusing requests that cannot be coordinated, sacrificing Availability (A).",
            "blooms_level": "Analyze",
            "difficulty": "medium"
        },
        {
            "qtype": "short_answer",
            "question": "Distinguish between Keynesian and Classical economic interpretations of the short-run aggregate supply curve elasticity.",
            "choices": [],
            "answer": "Keynesian models posit an upward-sloping short-run AS curve due to sticky nominal wages and prices, whereas Classical theory assumes rapid price-wage adjustment making AS vertical even in relatively short horizons.",
            "blooms_level": "Evaluate",
            "difficulty": "hard",
            "rationale": "Requires identifying wage/price rigidity and contrast of slope implications."
        }
    )
)

# 6. Postgraduate (Master's / PGD)
_POSTGRADUATE_PROFILE = PromptProfile(
    stage=Stage.POSTGRADUATE,
    audience_description="Graduate scholars pursuing master's degrees (MSc, MA, MBA) with advanced command of literature, research methodologies, and quantitative/qualitative synthesis.",
    language_and_reading_rules="""- High-level academic discourse reflecting current peer-reviewed research and theoretical debates.
- Focus on methodological validity, construct operationalization, causal inference, and paradigm tensions.
- Assume mastery of foundational undergraduate material.""",
    difficulty_guide={
        "easy": "Synthesis of competing literature perspectives or identifying assumptions underlying statistical/qualitative designs.",
        "medium": "Critiquing experimental controls, identifying confounding variables, or comparing empirical econometric/scientific strategies.",
        "hard": "Formulating alternative hypotheses for anomalous findings, meta-analytic critique, or addressing threats to internal/external validity.",
    },
    distractor_guidelines="""- Distractors must be sophisticated arguments that seem methodologically plausible but contain subtle inferential leaps, endogeneity traps, or overgeneralizations.""",
    default_blooms=("Analyze", "Evaluate", "Create"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "In observational causal inference, which condition will cause an Instrumental Variable (IV) estimator to suffer from severe finite-sample bias even in large samples?",
            "choices": [
                "Weak correlation between the instrument and the endogenous regressor (weak instrument)",
                "Heteroskedasticity in the structural error term",
                "Non-normality in the first-stage regression residuals",
                "Overidentification with multiple mutually uncorrelated valid instruments"
            ],
            "answer": "A",
            "rationale": "Weak instruments fail the rank condition adequately, leading to 2SLS bias towards the OLS estimator and inflated standard errors.",
            "blooms_level": "Evaluate",
            "difficulty": "hard"
        },
    )
)

# 7. Doctoral (PhD / Postdoctoral)
_DOCTORAL_PROFILE = PromptProfile(
    stage=Stage.DOCTORAL,
    audience_description="Doctoral researchers, PhD candidates, and postdocs operating at the frontier of scholarship, conducting original peer-reviewed inquiry and epistemological critique.",
    language_and_reading_rules="""- Scholarly peer-review standard.
- Target foundational assumptions, epistemological frameworks, paradigm limits, and boundary conditions.
- Test ability to dissect research methodologies, identify subtle logical fallacies in experimental arguments, and synthesize across divergent disciplines.""",
    difficulty_guide={
        "easy": "Dissecting theoretical presuppositions of dominant paradigm models or proving mathematical/structural bounds.",
        "medium": "Identifying subtle confounds, survivorship biases, or model identification failures in peer-reviewed findings.",
        "hard": "Evaluating contested theoretical paradigms, proposing novel falsification criteria, or defending methodological integrity under severe constraints.",
    },
    distractor_guidelines="""- Distractors must read like plausible peer-reviewer objections or widely held theoretical assumptions that fail under rigorous edge-case scrutiny.
- Absolutely no superficial or rote choices.""",
    default_blooms=("Evaluate", "Create", "Analyze"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "When assessing the validity of a regression discontinuity design (RDD), which diagnostic test provides the strongest empirical evidence against strategic sorting around the cutoff threshold?",
            "choices": [
                "McCrary density test confirming continuity of the running variable at the cutoff",
                "Durbin-Wu-Hausman test comparing 2SLS with OLS estimates",
                "Breusch-Pagan test verifying homoskedasticity of local polynomial residuals",
                "Granger causality test on lagged outcomes"
            ],
            "answer": "A",
            "rationale": "A discontinuity in the marginal density of the running variable (McCrary test) indicates non-random manipulation/sorting around the threshold, which violates the key identification assumption.",
            "blooms_level": "Evaluate",
            "difficulty": "hard"
        },
    )
)

# 8. Professional (Certifications / Continuing Professional Education)
_PROFESSIONAL_PROFILE = PromptProfile(
    stage=Stage.PROFESSIONAL,
    audience_description="Practicing professionals seeking licensing, board certification, or compliance mastery in applied industries.",
    language_and_reading_rules="""- Industry-standard terminology, codes of conduct, regulatory compliance, and practical decision-making.
- Scenario-based prompt framing: 'A client presents...', 'During a system audit, an engineer notices...'.
- Focus on practical judgment, risk mitigation, and standard operating procedures.""",
    difficulty_guide={
        "easy": "Direct application of ethical canons, mandatory statutory requirements, or standard compliance steps.",
        "medium": "Prioritizing remediation steps in a complex real-world incident or resolving competing client/business constraints.",
        "hard": "Managing high-risk non-compliance events, forensic root-cause analysis, or multi-jurisdictional regulatory conflicts.",
    },
    distractor_guidelines="""- Distractors should be commonly taken shortcuts, technically compliant but suboptimal practices, or actions that violate secondary professional safeguards.""",
    default_blooms=("Apply", "Analyze", "Evaluate"),
    few_shot_examples=(
        {
            "qtype": "mcq",
            "question": "Under the ISO 27001 risk management framework, what is the mandatory immediate next step after identifying and assessing an information security risk?",
            "choices": [
                "Formulate a Risk Treatment Plan selecting appropriate controls",
                "Immediately procure third-party cyber insurance",
                "Disconnect all affected network segments indefinitely",
                "Report the vulnerability to the public disclosure registry"
            ],
            "answer": "A",
            "rationale": "Following risk identification and assessment, ISO/IEC 27001 mandates defining a Risk Treatment Plan to accept, avoid, transfer, or mitigate risks with specific controls.",
            "blooms_level": "Apply",
            "difficulty": "medium"
        },
    )
)


PROMPT_PROFILES_BY_STAGE: Final[Mapping[Stage, PromptProfile]] = MappingProxyType({
    Stage.EARLY_YEARS: _EARLY_YEARS_PROFILE,
    Stage.PRIMARY: _PRIMARY_PROFILE,
    Stage.JUNIOR_SECONDARY: _JUNIOR_SEC_PROFILE,
    Stage.SENIOR_SECONDARY: _SENIOR_SEC_PROFILE,
    Stage.DIPLOMA: _DIPLOMA_PROFILE,
    Stage.UNDERGRADUATE: _UNDERGRADUATE_PROFILE,
    Stage.POSTGRADUATE: _POSTGRADUATE_PROFILE,
    Stage.DOCTORAL: _DOCTORAL_PROFILE,
    Stage.PROFESSIONAL: _PROFESSIONAL_PROFILE,
})


def get_prompt_profile(stage_or_level: Stage | EducationLevel) -> PromptProfile:
    """Retrieve the PromptProfile corresponding to an EducationLevel or Stage."""
    stage = stage_or_level.stage if isinstance(stage_or_level, EducationLevel) else stage_or_level
    return PROMPT_PROFILES_BY_STAGE.get(stage, _SENIOR_SEC_PROFILE)
