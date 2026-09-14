# Corporate Multimodal RAG Solution

## Revised RAG architecture flow

The router operates at page and subsection level. A single page may produce several evidence units, and one unit may receive more than one representation.

```mermaid
flowchart TD
    A[Source files and immutable versions] --> B[Parse, render and split into logical pages]
    B --> C[Identify sections and extraction quality]
    C --> D{Select representation per section}
    D --> T[Text index\nBM25 plus text embeddings]
    D --> V[Voyage multimodal\none vector for a region]
    D --> P[ColPali style\nmany visual patch vectors]
    T --> I[Governed retrieval indexes]
    V --> I
    P --> I
    Q[User question] --> R[Resolve permissions, brand, scope and as of date]
    R --> S[Search, fuse ranks and rerank]
    I --> S
    S --> E[Evidence pack: text, page crops, charts and footnotes]
    E --> G[Answer model with citations]
    R -.-> X[Approved rules engine]
    X -.-> E
    K[Catalog controls: approval, entitlements, version, supersession, provenance] -.-> B
    K -.-> I
    K -.-> S
    K -.-> G
```

**Boundary:** the approved rules engine determines eligibility. RAG retrieves and explains the supporting content; it does not derive rules at runtime.

---

## Slide 1: One governed library, three ways to find the right evidence

![Slide 1: One governed library, three ways to find the right evidence](images/slide-1.png)

---

## Slide 2: One brochure spread needs three retrieval treatments

![Slide 2: One brochure spread needs three retrieval treatments](images/slide-2.png)

---

## Slide 3: Embeddings turn content into numbers that search can compare

![Slide 3: Embeddings turn content into numbers that search can compare](images/slide-3.png)

---

## Slide 4: The system classifies sections before choosing how to index them

![Slide 4: The system classifies sections before choosing how to index them](images/slide-4.png)

---

## Slide 5: Search combines text and visual evidence before the AI answers

![Slide 5: Search combines text and visual evidence before the AI answers](images/slide-5.png)

---

## Slide 6: Governance decides what may be retrieved, used and shown

![Slide 6: Governance decides what may be retrieved, used and shown](images/slide-6.png)

---

