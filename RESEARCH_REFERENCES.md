# Research-backed Shorts and presenter layout

## Evidence pipeline
- `research_sources.py` queries PubMed's NCBI E-utilities for real indexed papers and stores title, journal, year, PMID, DOI, abstract, and canonical PubMed URL in `output/research_sources.json`.
- Gemini receives the retrieved abstracts as source material. It must keep claims within the abstract and return PMIDs selected from the supplied records only.
- Script validation rejects any PMID that was not retrieved during this run. References selected by the model are appended to the YouTube description by `gen_script.py`; `upload.py` uploads that description as-is.
- No fake or placeholder citation is generated when PubMed returns no matching record. In that case the script is instructed to stay conservative and use an empty sources list.
- PubMed is a research index, not a guarantee that each paper is high quality or directly applicable. Review the citations/claims before publication; abstracts are not full-text review.

## Presenter
The Shorts avatar is now smaller and in a top-right safe area, below the title and away from the central science diagram. Existing transparent mouth-state PNGs are still used for lip-sync.

## Artifacts
- `output/research_sources.json`: retrieved PubMed records
- `output/script.json`: script + selected references
- YouTube description: source title, journal/year, PMID, DOI (when indexed), and PubMed link
