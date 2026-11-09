"""Fetch real fitness evidence from PubMed (NCBI E-utilities); never fabricate citations."""
import json, os, re, time
import requests

BASE="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
HEADERS={"User-Agent":"FitFuelEducationalBot/1.0 (fitness evidence research)"}

def clean(s):
    return re.sub(r"\\s+"," ",str(s or "")).strip()

def fetch_pubmed(topic, limit=5):
    """Search PubMed and return verified PMID/title/year/DOI/abstract records."""
    if not topic: return []
    try:
        q=requests.get(BASE+"/esearch.fcgi",params={
            "db":"pubmed","term":topic+" AND (review[pt] OR randomized controlled trial[pt] OR meta-analysis[pt])",
            "retmax":limit,"sort":"relevance","retmode":"json"
        },headers=HEADERS,timeout=20)
        q.raise_for_status(); ids=q.json().get("esearchresult",{}).get("idlist",[])
        if not ids:
            q=requests.get(BASE+"/esearch.fcgi",params={"db":"pubmed","term":topic,"retmax":limit,"sort":"relevance","retmode":"json"},headers=HEADERS,timeout=20)
            q.raise_for_status(); ids=q.json().get("esearchresult",{}).get("idlist",[])
        if not ids:return []
        r=requests.get(BASE+"/efetch.fcgi",params={"db":"pubmed","id":",".join(ids),"retmode":"xml"},headers=HEADERS,timeout=30)
        r.raise_for_status()
        import xml.etree.ElementTree as ET
        root=ET.fromstring(r.text); out=[]
        for article in root.findall(".//PubmedArticle"):
            pmid=clean(article.findtext(".//PMID"))
            title=clean("".join(article.find(".//ArticleTitle").itertext())) if article.find(".//ArticleTitle") is not None else ""
            journal=clean(article.findtext(".//Journal/Title"))
            year=clean(article.findtext(".//PubDate/Year") or article.findtext(".//PubDate/MedlineDate"))[:4]
            abstract=" ".join(clean("".join(x.itertext())) for x in article.findall(".//Abstract/AbstractText"))
            doi=""
            for aid in article.findall(".//ArticleId"):
                if aid.attrib.get("IdType")=="doi":doi=clean(aid.text);break
            if pmid and title:
                out.append({"pmid":pmid,"title":title,"journal":journal,"year":year,"doi":doi,"abstract":abstract[:1800],
                  "url":"https://pubmed.ncbi.nlm.nih.gov/"+pmid+"/"})
        return out
    except Exception as exc:
        print("[research] PubMed unavailable:",str(exc)[:180])
        return []

def research_for_topic(topic):
    papers=fetch_pubmed(topic,5)
    os.makedirs("output",exist_ok=True)
    with open("output/research_sources.json","w",encoding="utf-8") as f:json.dump(papers,f,ensure_ascii=False,indent=2)
    print(f"[research] Retrieved {len(papers)} PubMed records for: {topic}")
    return papers

def references_block(papers):
    if not papers:return ""
    lines=["","\nSCIENTIFIC REFERENCES (PubMed):"]
    for i,p in enumerate(papers,1):
        citation=f"{i}. {p.get('title','')} ({p.get('journal','')}, {p.get('year','')}). PMID: {p['pmid']}."
        if p.get("doi"):citation+=" DOI: "+p["doi"]+"."
        citation+=" "+p["url"]
        lines.append(citation)
    return "\n".join(lines)
