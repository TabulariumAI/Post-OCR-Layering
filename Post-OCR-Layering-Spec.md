# Post-OCR Layering Spec

Prepared by Tabularium AI

- **Version:** 1.0
- **Status:** Published
- **Release date:** 2026-11-17
- **License:** [Apache License 2.0](LICENSE)


## Abstract

Post-OCR Layering is a deterministic, evidence-driven model for reconstructing document structure from recognized text and geometry. Each structural decision draws on two independent evidence sources: scale-normalized geometry from box coordinates, and paragraph ownership from OCR paragraph membership. They are resolved by an explicit precedence in which conclusive ownership outranks geometry. Agreement between the sources increases confidence in a decision; divergence is a diagnostic signal that flags risk without requiring ground truth. Thresholds are derived from each page's own statistics, decisions stay local to the zone their evidence supports, and reading order is a precedence graph with a deterministic result. Associations and order are auditable at every decision, and context preservation is scored separately from text preservation. This document presents the mathematical framework; recognition pipelines and parameter values are proprietary.

## Conformance and Normative Scope

Sections 1–8 and 11 define the normative layering, ordering, evaluation, and audit behavior. Sections 9–10 and all notes and examples are informative. A conforming implementation applies the hard-boundary and decision precedence in their stated order, produces the specified bundle partition and deterministic reading order, and produces the audit record required by Section 11. Machine-readable examples are published in [conformance](conformance/README.md).

## 1. Inputs

All structural decisions originate from two sources, defined below. Derived quantities are computed from these sources exclusively.

**Ω (Conventions and Parameters).** Instrument-type conventions (an instrument is a recorded document such as a deed or a mortgage): header and footer band fractions $η_h$, $η_f$ ∈ [0, 1), and the container types that set $b_i$ = 1. Calibrated parameters: θ, δ ≥ 0; ρ, $ρ_f$ ∈ (0, 1]; $\ell$ ≥ 2; $n_{min}$ ∈ ℕ; fallback tolerances α, β, γ ≥ 0 with multipliers $k_α$, $k_β$ > 0 and bounds [$α_{min}$, $α_{max}$], [$β_{min}$, $β_{max}$], [$γ_{min}$, $γ_{max}$]; default order π ∈ {row, col}; arc ranks ω(t) ∈ ℕ for t ∈ {region, column, row}; risk weights $λ_J$, $λ_S$, $λ_O$ ≥ 0 with $λ_J$ + $λ_S$ + $λ_O$ = 1.

**Ε (OCR Output).** Page width W and page height W′, in page coordinates with y increasing downward and text horizontal; skew and rotation are corrected before layering. For i = 1, …, n a word $v_i$ = ($id_i$, $text_i$, $B_i$, $S_i$), an ALTO String (ALTO is the XML standard for OCR text and layout), with unique, ordered $id_i$ and a container flag $b_i$ ∈ {0, 1}. Words are grouped into lines $Γ_1$, …, $Γ_N$ (ALTO TextLines). A paragraph set P and, for each p ∈ P, the union $Σ_p$ of its positive-length source intervals; without paragraph source spans, owner(i) = ⊥ for every word.

$$B_i = [x_i^-, x_i^+] \times [y_i^-, y_i^+], \qquad h_i = y_i^+ - y_i^-, \qquad w_i = x_i^+ - x_i^-$$

Where:

- $B_i$ - axis-aligned bounding box of word i (from Ε; ALTO: $x_i^-$ = HPOS, $x_i^+$ = HPOS + WIDTH, $y_i^-$ = VPOS, $y_i^+$ = VPOS + HEIGHT);
- $S_i$ - source spans of word i into the recognized text (from Ε); $h_i$, $w_i$ - height and width of word i;
- $Γ_j$ - j-th line, with left edge $x^-$($Γ_j$), right edge $x^+$($Γ_j$) and width w($Γ_j$) (from Ε);
- $b_i$ - 1 if word i lies inside a container type listed in Ω (for example a ruled box).

## 2. Definitions

Let D be a page under review. A **row** is a set of words sharing a physical row (Section 3.1). A **zone** is a stretch of the page between hard boundaries in which structure decisions apply (Section 5.1). A **run** is a sequence of paired rows within a zone (Section 5.2). A **bundle** is a set of words forming one paragraph unit (Section 6). The layering output for D is the set of run decisions d(Q), the bundle partition N̂, and the reading order pos.

The geometric unit of D is the median positive word height:

$$H = \mathrm{median}\{\, h_i : h_i > 0 \,\}$$

Every distance is expressed in units of H, which makes it invariant under uniform scaling:

$$\frac{a \cdot d}{a \cdot H} = \frac{d}{H}$$

Where:

- H - geometric unit of D (from Ε);
- d - any distance on the page; a > 0 - any uniform scale factor.

A zone is decidable iff it contains a run. Zones without a run are processed by region order only.

## 3. Geometric Model

### 3.1 Rows

Two words are row-compatible when their vertical overlap covers at least a fraction θ of the shorter word. A row is a maximal set of words connected by row compatibility. Vertical gaps are measured in units of H:

$$q_y(i,j) = \frac{\max\big(0,\ \min(y_i^+, y_j^+) - \max(y_i^-, y_j^-)\big)}{\min(h_i, h_j)}$$

$$g_y(i,j) = \frac{y_j^- - y_i^+}{H}, \qquad g_{row}(m) = \frac{y_{m+1}^- - y_m^+}{H}$$

Where:

- $q_y$ - row compatibility ∈ [0, 1]; two words are row-compatible iff $q_y$ ≥ θ;
- $g_y$ - normalized vertical gap between words i and j;
- $y_m^-$, $y_m^+$ - top of the highest and bottom of the lowest word in row m; $g_{row}$(m) - gap between row m and row m + 1.

Note: A high $q_y$ supports a shared physical row. It does not establish that the words are concatenated.

### 3.2 Page-Derived Thresholds

The gutter, alignment and spacing tolerances are derived from each page's own statistics. The minimum gutter is the split of the page's normalized horizontal word gaps that best separates gaps inside a line from gaps between columns:

$$\hat\gamma_0 = \arg\max_{t \in D_h} \; w_0(t)\, w_1(t)\, \big(\mu_0(t) - \mu_1(t)\big)^2$$

$$\hat\alpha_0 = \frac{k_\alpha\, m_x}{H}, \qquad m_x = \mathrm{median}\{\, |x^-(\Gamma_j) - x_{body}^-| : w(\Gamma_j) \ge \rho W \,\}$$

$$\hat\beta_0 = k_\beta \cdot \mathrm{median}\{\, g_{row}(m) : g_{row}(m) > 0 \,\}$$

Each derived value is bounded, and falls back to its calibrated value when its sample is too small:

$$\hat\gamma = \begin{cases} \mathrm{clip}(\hat\gamma_0,\ \gamma_{min},\ \gamma_{max}) & |D_h| \ge n_{min} \\ \gamma & \text{otherwise} \end{cases}$$

α̂ and β̂ take the same form, with samples |{j : w($Γ_j$) ≥ ρW}| and |{m : $g_{row}$(m) > 0}|.

Where:

- $D_h$ - normalized horizontal gaps ($x_j^-$ − $x_i^+$) / H between neighboring words i and j in one row; t - candidate split value; ρ - long-line ratio (from Ω); W - page width (from Ε);
- $w_0$(t), $w_1$(t) - fractions of $D_h$ at or below t and above t; $μ_0$(t), $μ_1$(t) - the means of those two classes;
- $m_x$ - median deviation of long-line left edges from the body-track edge $x_{body}^-$ (Section 3.3);
- $k_α$, $k_β$ - multipliers (from Ω); $n_{min}$ - minimum sample size (from Ω); γ - calibrated fallback (from Ω);
- γ̂, α̂, β̂ - minimum gutter, alignment tolerance and spacing tolerance in units of H.

In Sections 5 and 6, α, β, γ denote α̂, β̂, γ̂.

Note: The statistics come from the page being interpreted. The bounds and the fallback keep a page made only of paired fields from shifting its own baseline.

### 3.3 Regions

A word's region follows from page position. Header and footer are bands of the page height, and side margins lie beyond the main text track:

$$r_i = \begin{cases} \text{header} & y_i^+ \le \eta_h W' \\ \text{footer} & y_i^- \ge (1 - \eta_f) W' \\ \text{body} & \text{otherwise} \end{cases}$$

$$x_{body}^- = \mathrm{median}\{\, x^-(\Gamma_j) : w(\Gamma_j) \ge \rho W \,\}, \qquad x_{body}^+ = \mathrm{median}\{\, x^+(\Gamma_j) : w(\Gamma_j) \ge \rho W \,\}$$

$$reg(i) = \begin{cases} \text{margin-left} & x_i^+ < x_{body}^- - \delta H \\ \text{margin-right} & x_i^- > x_{body}^+ + \delta H \\ r_i & \text{otherwise} \end{cases}$$

Where:

- $η_h$, $η_f$ - header and footer band fractions per instrument type (from Ω), following prevailing practice in official records;
- $x_{body}^-$, $x_{body}^+$ - left and right bounds of the main text track; a page without long lines has no margins;
- ρ - long-line ratio (from Ω); δ - margin safety distance in units of H (from Ω).

Note: A margin is a position and a role is a structural label. They are never equated.

## 4. Ownership Evidence

Let $Z_i$ be the source positions covered by word i. The paragraphs covering source position z are C(z), and a word has a determined owner only when every position it covers belongs to one and the same paragraph:

$$C(z) = \{\, p \in P : z \in \Sigma_p \,\}$$

$$owner(i) = \begin{cases} p & Z_i \ne \emptyset \ \land\ C(z) = \{p\}\ \ \forall z \in Z_i \\ \bot & \text{otherwise} \end{cases}$$

Where:

- P - set of OCR paragraphs (from Ε); $Σ_p$ - source intervals of paragraph p (from Ε);
- $Z_i$ - source positions covered by word i; C(z) - paragraphs covering position z;
- ⊥ - undetermined owner; missing coverage or overlapping paragraphs yield ⊥.

Note: Paragraph membership is evidence already present in the OCR output, and it comes from a domain disjoint from box geometry.

## 5. Decision Logic

### 5.1 Hard Boundary

Evaluated before any pairing decision. A word is a hard boundary when its line is full-width or it lies inside a container:

$$hb(i) \iff w(\Gamma(i)) \ge \rho_f W \ \lor\ b_i = 1$$

Where:

- Γ(i) - line containing word i; $ρ_f$ - full-width ratio (from Ω);
- $b_i$ - container flag (from Ε).

A zone U is a maximal run of consecutive words in one region between hard boundaries. A hard boundary terminates every zone unconditionally, a decision made in a zone never applies outside it, and no global column count is imposed on the page.

### 5.2 Run Construction

Let a zone contain consecutive rows $U_1$, …, $U_K$ with K ≥ $\ell$. The coverage at horizontal position x is:

$$\mathrm{cov}(x) = \big|\{\, i \in U_1 \cup \dots \cup U_K : x_i^- < x < x_i^+ \,\}\big|$$

The gutter is the widest open interval ($g^-$, $g^+$), between the leftmost and rightmost word edges of these rows, on which cov(x) = 0. It exists only if the interval has positive width. The left and right groups are:

$$L = \{\, i : x_i^+ \le g^- \,\}, \qquad R = \{\, i : x_i^- \ge g^+ \,\}$$

A run Q is a maximal sequence of consecutive rows that each hold at least one word of L and one of R. For row m of Q, with $a_m$, $b_m$ the starting and ending edge of the left group and $c_m$ the starting edge of the right group:

$$a_m = \min\{x_i^- : i \in U_m \cap L\}, \quad b_m = \max\{x_i^+ : i \in U_m \cap L\}, \quad c_m = \min\{x_i^- : i \in U_m \cap R\}$$

$$\Delta_L = \max_m a_m - \min_m a_m, \qquad \Delta_R = \max_m c_m - \min_m c_m, \qquad G = \min_m c_m - \max_m b_m$$

Where:

- cov(x) - number of words covering position x; ($g^-$, $g^+$) - gutter;
- $Δ_L$, $Δ_R$ - starting-edge spreads of the left and right groups; G - gutter shared by the whole run;
- $\ell$ - minimum number of rows (from Ω).

### 5.3 Evidence Predicates

Geometric evidence, from box coordinates:

$$Geo(Q) \iff \Delta_L \le \alpha H \ \land\ \Delta_R \le \alpha H \ \land\ G \ge \gamma H \ \land\ \max_m g_{row}(m) \le \beta$$

Ownership evidence, from OCR paragraph membership. Let $P_L$, $P_R$ be the owners of the left and right words of Q, and $N_L$(p), $N_R$(p) the number of rows of Q holding a left or right word owned by p:

$$Col(Q) \iff \bot \notin P_L \cup P_R \ \land\ P_L \cap P_R = \emptyset \ \land\ \exists p \in P_L : N_L(p) \ge \ell \ \land\ \exists p \in P_R : N_R(p) \ge \ell$$

$$Row(Q) \iff \bot \notin P_L \cup P_R \ \land\ P_L = P_R = \{p\} \ \land\ |Q| \ge \ell$$

Where:

- Geo(Q) - aligned starting edges, a persistent gutter and limited row gaps; α, β, γ - tolerances (Section 3.2);
- Col(Q) - separate multiline paragraphs on the two sides; Row(Q) - one paragraph owning both sides over the whole run;
- |Q| - number of rows in Q.

Note: Col(Q) and Row(Q) are mutually exclusive. Geo(Q) is neutral between paired fields and parallel paragraphs, which both produce aligned edges and a gutter.

### 5.4 Zone Decision

In strict order of precedence:

$$d(Q) = \begin{cases} \text{col} & Col(Q) \\ \text{row} & Row(Q) \\ \pi & \neg Col(Q) \land \neg Row(Q) \land Geo(Q) \\ \text{unpaired} & \text{otherwise} \end{cases}$$

Where:

- d(Q) = col - the left and right groups are independent columns; d(Q) = row - the groups are paired fields;
- π - the default order (from Ω), applied and recorded when ownership is inconclusive;
- unpaired - no pairing is established, and the rows follow region order only.

Note: Conclusive ownership outranks geometry, and geometry alone never overrides it.

### 5.5 Evidence Agreement

The two sources come from disjoint domains: Geo(Q) from box coordinates, Col(Q) and Row(Q) from OCR paragraph membership. Their relation is a diagnostic:

$$Agree(Q) \iff Geo(Q) \land \big(Col(Q) \lor Row(Q)\big)$$

$$Diverge(Q) \iff \neg Geo(Q) \land \big(Col(Q) \lor Row(Q)\big)$$

$$Open(Q) \iff \neg Col(Q) \land \neg Row(Q)$$

Where:

- Agree(Q) - both sources support the decision; confidence is high;
- Diverge(Q) - ownership is conclusive but the geometry is irregular; the decision follows ownership and is flagged;
- Open(Q) - ownership is inconclusive; the decision follows geometry and π, or is unpaired, and is flagged.

Note: Agreement and divergence require no ground truth.

## 6. Bundles

Let side(i) ∈ {L, R, none} be the side of word i in a decided run Q, with none outside any run. Two words join when they share a zone, a region and compatible ownership, and are continuous on the page:

$$Join(i,j) \iff U(i) = U(j) \ \land\ reg(i) = reg(j) \ \land\ Own(i,j) \ \land\ \big( Same(i,j) \lor Cross(i,j) \big)$$

$$Own(i,j) \iff \neg\big( owner(i) \ne \bot \land owner(j) \ne \bot \land owner(i) \ne owner(j) \big)$$

$$Same(i,j) \iff side(i) = side(j) \ \land\ 0 \le g_y(i,j) \le \beta \ \land\ |x_i^- - x_j^-| \le \alpha H$$

$$Cross(i,j) \iff side(i) \ne side(j) \ \land\ d(Q) = \text{row} \ \land\ q_y(i,j) \ge \theta$$

Bundles are the connected components of the graph whose edges are admissible joins.

Where:

- U(i) - zone of word i; Own - two determined owners must match, and an undetermined owner is compatible;
- Same - continuity within one side; Cross - pairing across sides, allowed only when the run decision is row.

Note: An isolated indentation fails Same by α and is weak evidence: it may introduce a separate block, an address continuation or a wrapped field value.

## 7. Reading Order

Bundles are the nodes of a precedence graph, and each arc carries a type t ∈ {region, column, row}. Region arcs order header $\prec$ body $\prec$ footer $\prec$ margin-left $\prec$ margin-right; column arcs place every bundle on the left side of a run with d(Q) = col before every bundle on the right; row arcs place row m before row m + 1 within a zone. The accepted arcs must be acyclic. While a cycle exists, the arc of lowest rank ω(t) in the first cycle found by a depth-first traversal in ascending bundle id is removed, and equal ranks remove the smaller arc id. At each step the output emits the available bundle with the smallest key:

$$key(X) = \big(\, y_X^-,\ x_X^-,\ id_X \,\big), \qquad (X, Y, t) \in A \ \Rightarrow\ pos(X) < pos(Y)$$

Where:

- A - accepted arcs after cycle resolution; ω(t) - priority rank of arc type t (from Ω; higher is kept);
- $y_X^-$, $x_X^-$ - top and left edge of bundle X; $id_X$ - smallest word id in X; pos(X) - position of X in the output.

Note: The key makes the output repeatable.

## 8. Evaluation

Context preservation is scored per fragment against an independently established reference. Let N\* be the reference bundle partition, N̂ the predicted partition, and N\*(i), N̂(i) the bundles containing word i:

$$Prec = \frac{1}{n}\sum_{i=1}^{n} \frac{|\hat N(i) \cap N^{\ast}(i)|}{|\hat N(i)|}, \qquad Rec = \frac{1}{n}\sum_{i=1}^{n} \frac{|\hat N(i) \cap N^{\ast}(i)|}{|N^{\ast}(i)|}$$

$$O = \frac{|\{ (X,Y) \in A^{\ast} : pos(X) > pos(Y) \}|}{|A^{\ast}|}$$

$$Risk = \lambda_J (1 - Prec) + \lambda_S (1 - Rec) + \lambda_O \, O, \qquad Risk \in [0, 1]$$

Where:

- n - number of words; 1 − Prec - false-join rate; 1 − Rec - false-split rate;
- A\* - reference precedence relations; O - fraction of them violated by the output (O = 0 when A\* = $\emptyset$);
- $λ_J$, $λ_S$, $λ_O$ - task-dependent weights (from Ω).

A false join creates an association the document never established; a false split removes one it needed. Binding an amount to the wrong obligation, or detaching a party from its role, costs more than splitting an address across adjacent blocks, and the weights state that cost. Text preservation, the equality of recognized tokens, is scored separately from Prec, Rec and O.

The calibrated parameters Θ are set per instrument type on a reference set $\mathcal{D}$ of labeled pages by minimizing mean Risk:

$$\Theta^{\ast} = \arg\min_{\Theta} \; \frac{1}{|\mathcal{D}|} \sum_{D \in \mathcal{D}} Risk(D;\, \Theta)$$

Where:

- Θ - the calibrated parameters of Ω (θ, ρ, $ρ_f$, δ, $\ell$, $n_{min}$, the multipliers and bounds for α̂, β̂, γ̂, the ranks ω and the default π);
- $\mathcal{D}$ - reference set of pages with established N\* and A\*; $λ_J$, $λ_S$, $λ_O$ are set by task cost and are not estimated.

## 9. Comparative Evaluation

Extraction quality is the document-level score, from 0% to 100%, of the index fields that downstream LLM processing extracts from the layered text; each field is weighted by its importance and reduced by extraction confidence and ambiguity. Effectiveness is measured by extraction quality and by comparing page images with the layered results. Four approaches were compared on official records:

| Approach | Extraction quality |
|---|---|
| No layering: ALTO sent to the LLM as JSON | 86% to 92% |
| General-purpose services with prebuilt layering (Microsoft, Amazon) | 94% to 96% |
| AI-based layering | 96% to 98.6% |
| Post-OCR Layering | 96% to 100%, typically 97% to 98% |

Post-OCR Layering raises the minimum extraction quality from 86% to 96% over the unprocessed baseline and reaches the highest maximum, 100%. AI-based layering reaches a comparable range, but no model trained specifically for official records was found among those compared; the closest, trained for legal documents, came close to the results of Post-OCR Layering and did not exceed them.

## 10. Worked Example

One zone, one run of three paired rows. Numbers illustrative; deployments derive tolerances per page.

H = 10. Tolerances: α = 0.5, β = 1.5, γ = 3, $\ell$ = 2.

| Row m | $y^-$ | $y^+$ | $a_m$ | $b_m$ | $c_m$ |
|---|---|---|---|---|---|
| 1 | 100 | 110 | 72 | 180 | 300 |
| 2 | 120 | 130 | 73 | 195 | 302 |
| 3 | 140 | 150 | 72 | 170 | 301 |

Applying the definitions:

$$\begin{aligned}
\Delta_L &= 73 - 72 = 1 \le \alpha H = 5\\
\Delta_R &= 302 - 300 = 2 \le \alpha H = 5\\
G &= 300 - 195 = 105 \ge \gamma H = 30\\
g_{row}(1) &= g_{row}(2) = \frac{120 - 110}{10} = 1 \le \beta = 1.5
\end{aligned}$$

Geo(Q) holds. The geometry is identical in the three cases below, and ownership decides:

- Case A: $P_L$ = $P_R$ = {p₃} over all three rows. Row(Q) holds, so d(Q) = row, and Agree(Q) holds.
- Case B: $P_L$ = {p₁}, $P_R$ = {p₂}, each spanning all three rows, so $N_L$(p₁) = $N_R$(p₂) = 3 ≥ $\ell$. Col(Q) holds, so d(Q) = col, and Agree(Q) holds.
- Case C: one word has owner ⊥. Neither Col(Q) nor Row(Q) holds, so d(Q) = π, and Open(Q) holds.

## 11. Auditability

Every layering run produces a complete audit record: the page statistics with the derived tolerances α̂, β̂, γ̂, their sample sizes, and whether each fell back to its calibrated value; per run Q, the decision d(Q), its evidence source (ownership, geometry or default π), the agreement state (Agree, Diverge or Open) and the values $Δ_L$, $Δ_R$, G/H, max $g_{row}$, $P_L$ and $P_R$; per pair of words, the Join conditions evaluated and any that failed; per reading order, every arc removed during cycle resolution with its type and rank ω(t); and, where reference data exists, Prec, Rec, O and Risk. For Diverge and Open decisions: reason codes identifying ⊥ ownership, a failed Geo(Q) clause, or a fallback to π.

## Version History

v1.0: Core post-OCR layering model, ownership evidence, page-derived thresholds and evaluation framework.
