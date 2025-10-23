import os
import json
import requests
from datetime import datetime
import re

# Configurazione
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')

# Query mirate per Google Search (NON News)
SEARCH_QUERIES = [
    # Problemi tecnici
    "EDM wire break problem solution",
    "wire EDM troubleshooting guide",
    "EDM surface finish improvement",
    
    # Novità aziende
    "Sodick new EDM machine 2025",
    "GF Machining Solutions latest EDM",
    "Mitsubishi EDM innovation",
    
    # Applicazioni
    "EDM aerospace machining",
    "medical device EDM manufacturing",
    
    # Forum e community
    "site:practicalmachinist.com EDM",
    "site:cnczone.com wire EDM"
]

CATEGORIES = [
    "Problemi e Soluzioni",
    "Nuovi Modelli",
    "Innovazioni Tecnologiche",
    "Eventi e Fiere",
    "Applicazioni e Mercato"
]

def search_with_serpapi(query):
    """Cerca usando SerpAPI - accesso completo a Google Search"""
    
    if not SERPAPI_KEY:
        print("   ⚠️ SERPAPI_KEY non configurata")
        return []
    
    try:
        url = "https://serpapi.com/search"
        
        params = {
            'q': query,
            'api_key': SERPAPI_KEY,
            'engine': 'google',
            'num': 5,  # Primi 5 risultati
            'gl': 'us',
            'hl': 'en'
        }
        
        response = requests.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Estrai risultati organici
            for result in data.get('organic_results', [])[:5]:
                results.append({
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'url': result.get('link', ''),
                    'source': result.get('displayed_link', 'Web'),
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            
            return results
        else:
            print(f"   ⚠️ SerpAPI error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"   ⚠️ Errore SerpAPI: {e}")
        return []

def search_google_fallback(query):
    """Fallback: Cerca usando DuckDuckGo (gratis, no API)"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        
        # Risultato principale
        if data.get('AbstractText'):
            results.append({
                'title': data.get('Heading', query),
                'snippet': data.get('AbstractText', ''),
                'url': data.get('AbstractURL', ''),
                'source': data.get('AbstractSource', 'DuckDuckGo'),
                'date': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Related topics
        for topic in data.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append({
                    'title': topic.get('Text', '')[:100],
                    'snippet': topic.get('Text', ''),
                    'url': topic.get('FirstURL', ''),
                    'source': 'DuckDuckGo',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
        
        return results
    except Exception as e:
        print(f"   ⚠️ Errore DuckDuckGo: {e}")
        return []

def analyze_with_gemini(all_results):
    """Analizza con Gemini"""
    
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY non configurata")
        return analyze_locally(all_results)
    
    if len(all_results) == 0:
        return {"notizie": []}
    
    # Prepara contenuto
    content_summary = []
    for result in all_results[:20]:
        content_summary.append(
            f"Titolo: {result.get('title', '')}\n"
            f"Descrizione: {result.get('snippet', '')}\n"
            f"Fonte: {result.get('source', '')}\n"
        )
    
    combined_content = "\n---\n".join(content_summary)
    
    prompt = f"""Analizza questi contenuti sulle macchine EDM (Electrical Discharge Machining).

CONTENUTI:
{combined_content}

FOCUS:
- Problemi tecnici e soluzioni pratiche
- Nuovi prodotti e modelli
- Innovazioni tecnologiche
- Eventi e fiere
- Applicazioni nei vari settori

Crea notizie in ITALIANO, focus su:
- Cosa significa per chi usa macchine EDM
- Benefici pratici
- Soluzioni a problemi comuni

CATEGORIE: Problemi e Soluzioni, Nuovi Modelli, Innovazioni Tecnologiche, Eventi e Fiere, Applicazioni e Mercato

Rispondi SOLO in JSON:
{{
  "notizie": [
    {{
      "titolo": "titolo chiaro in italiano",
      "categoria": "una categoria",
      "riassunto": "spiegazione pratica in italiano (2-3 frasi)",
      "importanza": 7,
      "fonte": "nome fonte",
      "data": "2025-10-22"
    }}
  ]
}}"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 3000}
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*', '', text).strip()
                return json.loads(text)
        
        print("⚠️ Gemini non disponibile, analisi locale")
        return analyze_locally(all_results)
            
    except Exception as e:
        print(f"⚠️ Errore Gemini: {e}")
        return analyze_locally(all_results)

def analyze_locally(results):
    """Analisi locale semplice"""
    notizie = []
    
    for result in results:
        notizie.append({
            'titolo': result.get('title', 'Notizia EDM')[:120],
            'categoria': 'Applicazioni e Mercato',
            'riassunto': result.get('snippet', '')[:300],
            'importanza': 6,
            'fonte': result.get('source', 'Web'),
            'data': result.get('date', datetime.now().strftime('%Y-%m-%d'))
        })
    
    return {'notizie': notizie}

def save_results(notizie, filename='data/edm_news.json'):
    """Salva risultati"""
    os.makedirs('data', exist_ok=True)
    
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    new_entry = {
        'timestamp': datetime.now().isoformat(),
        'data': {'notizie': notizie}
    }
    existing_data.append(new_entry)
    existing_data = existing_data[-100:]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Risultati salvati in {filename}")

def main():
    print("🤖 Avvio Agente EDM - Ricerca con SerpAPI")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_results = []
    
    # Determina quale motore usare
    use_serpapi = bool(SERPAPI_KEY)
    use_fallback = not use_serpapi
    
    if use_serpapi:
        print("✓ Uso SerpAPI (Google Search completo)")
    else:
        print("⚠️ SERPAPI_KEY non trovata, uso DuckDuckGo (limitato)")
    
    print("\n🔍 Ricerca in corso...")
    
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"\n[{i}/{len(SEARCH_QUERIES)}] {query}")
        
        if use_serpapi:
            results = search_with_serpapi(query)
        else:
            results = search_google_fallback(query)
        
        if results:
            all_results.extend(results)
            print(f"   ✓ Trovati {len(results)} risultati")
        else:
            print(f"   ⚠ Nessun risultato")
    
    print(f"\n📊 Totale risultati: {len(all_results)}")
    
    if len(all_results) == 0:
        print("\n❌ Nessun risultato trovato")
        print("💡 Suggerimenti:")
        print("   - Verifica SERPAPI_KEY in GitHub Secrets")
        print("   - Controlla quota SerpAPI su serpapi.com/dashboard")
        save_results([])
        return
    
    # Rimuovi duplicati
    seen = set()
    unique_results = []
    for r in all_results:
        key = r['title'][:60].lower()
        if key not in seen and key.strip():
            seen.add(key)
            unique_results.append(r)
    
    print(f"📊 Risultati unici: {len(unique_results)}")
    
    # Analisi
    print("\n🧠 Analisi con Gemini...")
    analyzed = analyze_with_gemini(unique_results)
    notizie = analyzed.get('notizie', [])
    
    if notizie:
        notizie.sort(key=lambda x: x.get('importanza', 0), reverse=True)
        save_results(notizie[:15])
        
        print(f"\n✨ Salvate {len(notizie[:15])} notizie!")
        
        print("\n📰 Top 5:")
        for i, news in enumerate(notizie[:5], 1):
            print(f"{i}. [{news.get('importanza')}/10] {news.get('titolo')[:70]}...")
    else:
        print("\n⚠️ Nessuna notizia rilevante")
        save_results([])
    
    print("\n✅ Completato!")

if __name__ == "__main__":
    main()
