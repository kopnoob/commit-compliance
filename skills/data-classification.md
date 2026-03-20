---
name: data-classification
description: "Classify data sensitivity and recommend the appropriate tier. Use this skill when working with files that might contain personal data, health information, financial data, or other sensitive content."
---

# Data Classification Skill

When the user is working with data or files that may be sensitive, help them classify the data and recommend the appropriate processing tier.

## Classification levels

### 🔴 STRENGT FORTROLIG (Tier 1 — Lokal/Norsk jord anbefalt)
- Helseopplysninger (journaler, diagnoser, resepter)
- Data underlagt sikkerhetsloven
- Forsvarsrelatert informasjon
- Biometriske data
- Data som eksplisitt krever norsk jurisdiksjon per kontrakt

**Anbefaling:** Bruk lokal inferens (Ollama) eller behandle manuelt. Ikke send via noen sky-API.

### 🟡 FORTROLIG (Tier 2 — EU Bedrock anbefalt)
- Personnummer, fødselsdato, adresser
- Ansattdata, lønnsopplysninger
- Kunderegistre med personopplysninger
- Finansielle data (kontonumre, transaksjoner)
- Kontraktsinformasjon med persondata
- Helse-relaterte data som er pseudonymisert

**Anbefaling:** Bytt til EU tier (`/commit:tier eu`) før behandling. Data forblir innenfor EU.

### 🟢 INTERN (Tier 2 eller 3)
- Intern forretningsdokumentasjon uten persondata
- Kildekode (med mindre den inneholder hardkodet PII)
- Teknisk dokumentasjon
- Aggregerte/anonymiserte data
- Offentlig tilgjengelig informasjon

**Anbefaling:** EU tier er trygt. Global tier er akseptabelt hvis ingen persondata er involvert.

### ⚪ OFFENTLIG (Tier 3 — Global OK)
- Open source-kode
- Offentlige dokumenter
- Generelle spørsmål uten kontekstdata
- Læring og research

**Anbefaling:** Bruk global tier for best ytelse og lavest kostnad.

## Når du klassifiserer

1. Les filnavn og innhold (om tilgjengelig)
2. Sjekk for PII-mønstre (fødselsnumre, navn+adresse-kombinasjoner, helsetermer)
3. Vurder konteksten — en fil som heter `patients.csv` er sannsynligvis sensitiv selv om du ikke ser PII direkte
4. Presenter klassifiseringen og tier-anbefalingen tydelig
5. Spør brukeren om bekreftelse før du behandler data i en lavere tier enn anbefalt
