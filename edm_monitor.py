import os
import json
import requests
from datetime import datetime
import re

# Configurazione
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')

# Query mirate
SEARCH_QUERIES = [
    "EDM wire break problem solution",
    "wire EDM troubleshooting guide",
    "Sodick new EDM machine 2025",
    "GF Machining Solutions latest EDM",
    "Mitsubishi EDM innovation",
    "EDM aerospace machining",
    "medical device EDM manufacturing",
    "site:practicalmachinist.com EDM",
    "site:cnczone.com wire EDM",
    "EDM automation Industry 4.0"
]

CATEGORIES = {
    'problem': 'Problemi e Soluzioni',
    'new_model': 'Nuovi Modelli',
    'technology': 'Innovazioni Tecnologiche',
    'event': 'Eventi e Fiere',
    'application': 'Applicazioni e Mercato'
}

CATEGORY_KEYWORDS = {
    'Problemi e Soluzioni': [
        'problem', 'troubleshooting', 'issue', 'error', 'fix', 'solution',
        'repair', 'maintenance', 'break', 'failure', 'problema', 'riparazione'
    ],
    'Nuovi Modelli': [
        'new', 'launch', 'introduce', 'release', 'model', 'series',
        'announce', 'unveil', 'nuovo', 'lancio', 'presentazione'
    ],
    'Innovazioni Tecnologiche': [
        'innovation', 'technology', 'AI', 'automation', 'smart', 'digital',
        'IoT', 'advanced', 'precision', 'breakthrough', 'innovazione'
    ],
    'Eventi e Fiere': [
        'event', 'fair', 'exhibition', 'show', 'conference', 'EMO', 'IMTS',
        'JIMTOF', 'fiera', 'evento', 'mostra'
    ],
    'Applicazioni e Mercato': [
        'aerospace', 'medical', 'automotive', 'industry', 'market',
        'application', 'manufacturing', 'production', 'applicazione'
    ]
}

HIGH_IMPORTANCE = [
    'breakthrough', 'revolutionary', 'first', 'major', 'significant',
    'innovative', 'advanced', 'new technology', 'patent', 'award'
]

MEDIUM_IMPORTANCE = [
    'improved', 'enhanced', 'optimized', 'updated', 'upgraded',
    'better', 'faster', 'efficient'
]

def search_with_serpapi(query):
    """Cerca usando SerpAPI"""
    if not SERPAPI_KEY:
        return []
    
    try:
        url = "https://serpapi.com/search"
        params = {
            'q': query,
            'api_key': SERPAPI_KEY,
            'engine': 'google',
            'num': 5,
            'gl': 'us',
            'hl': 'en'
        }
        
        response = requests.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for result in data.get('organic_results', [])[:5]:
                results.append({
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'url': result.get('link', ''),
                    'source': result.get('displayed_link', 'Web'),
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            
            return results
        
        return []
            
    except Exception as e:
        print(f"   ⚠️ Errore: {e}")
        return []

def analyze_with_gemini(all_results):
    """Usa Gemini per analizzare (se disponibile)"""
    
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY non configurata, uso analisi locale")
        return None
    
    if len(all_results) == 0:
        return None
    
    # Prepara contenuto
    content_summary = []
    for result in all_results[:20]:
        content_summary.append(
            f"Titolo: {result.get('title', '')}\n"
            f"Descrizione: {result.get('snippet', '')}\n"
            f"URL: {result.get('url', '')}\n"
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

IMPORTANTE: Mantieni gli URL originali per ogni notizia.

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
      "data": "2025-10-23",
      "url": "URL originale completo"
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
        
        print("⚠️ Gemini non disponibile")
        return None
            
    except Exception as e:
        print(f"⚠️ Errore Gemini: {e}")
        return None

def categorize_smart(text):
    """Categorizzazione intelligente"""
    text_lower = text.lower()
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(2 if keyword in text_lower else 0 for keyword in keywords)
        scores[category] = score
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    
    return 'Applicazioni e Mercato'

def calculate_importance_smart(text):
    """Calcola importanza"""
    text_lower = text.lower()
    score = 5
    
    for keyword in HIGH_IMPORTANCE:
        if keyword in text_lower:
            score += 2
    
    for keyword in MEDIUM_IMPORTANCE:
        if keyword in text_lower:
            score += 1
    
    brands = ['sodick', 'mitsubishi', 'gf machining', 'makino', 'fanuc', 'agie']
    if any(brand in text_lower for brand in brands):
        score += 1
    
    if re.search(r'\d+%|\d+x|€\d+|\$\d+', text):
        score += 1
    
    return min(score, 10)

def clean_and_summarize(snippet):
    """Pulisce snippet"""
    snippet = re.sub(r'[^\w\s\.,;:()\-\'\"!?€$%]', '', snippet)
    
    if len(snippet) > 280:
        truncated = snippet[:280]
        last_period = truncated.rfind('.')
        if last_period > 200:
            snippet = truncated[:last_period + 1]
        else:
            snippet = truncated + '...'
    
    return snippet.strip()

def translate_title(title):
    """Traduzione parziale"""
    translations = {
        'New': 'Nuovo',
        'Latest': 'Ultimo',
        'Innovation': 'Innovazione',
        'Technology': 'Tecnologia',
        'Problem': 'Problema',
        'Solution': 'Soluzione',
        'Guide': 'Guida',
        'Troubleshooting': 'Risoluzione Problemi',
        'Advanced': 'Avanzato',
        'Machine': 'Macchina',
        'Manufacturing': 'Produzione'
    }
    
    title_translated = title
    for eng, ita in translations.items():
        title_translated = re.sub(r'\b' + eng + r'\b', ita, title_translated, flags=re.IGNORECASE)
    
    return title_translated

def clean_source(source):
    """Pulisce la fonte da caratteri speciali"""
    # Rimuovi caratteri speciali comuni
    source = source.replace('›', '/').replace('»', '/').replace('…', '...')
    source = re.sub(r'[<>]', '', source)
    return source.strip()

def analyze_locally_enhanced(results):
    """Analisi locale migliorata"""
    notizie = []
    
    for result in results:
        title = result.get('title', 'Notizia EDM')
        snippet = result.get('snippet', '')
        combined = f"{title} {snippet}"
        
        edm_terms = ['edm', 'electrical discharge', 'wire edm', 'sodick', 
                     'mitsubishi', 'gf machining', 'makino', 'electrode']
        
        if not any(term in combined.lower() for term in edm_terms):
            continue
        
        categoria = categorize_smart(combined)
        importanza = calculate_importance_smart(combined)
        riassunto = clean_and_summarize(snippet)
        titolo_translated = translate_title(title[:120])
        
        # Pulisci URL e fonte
        url = result.get('url', '').strip()
        fonte = clean_source(result.get('source', 'Web'))
        
        notizia = {
            'titolo': titolo_translated,
            'categoria': categoria,
            'riassunto': riassunto,
            'importanza': importanza,
            'fonte': fonte,
            'data': result.get('date', datetime.now().strftime('%Y-%m-%d')),
            'url': url
        }
        
        notizie.append(notizia)
    
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
    print("🤖 Avvio Agente EDM - Versione Completa")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not SERPAPI_KEY:
        print("❌ SERPAPI_KEY non configurata!")
        return
    
    has_gemini = bool(GOOGLE_API_KEY)
    print(f"✓ SerpAPI: Attivo")
    print(f"✓ Gemini AI: {'Attivo' if has_gemini else 'Non disponibile (uso analisi locale)'}")
    
    print("\n🔍 Ricerca in corso...")
    
    all_results = []
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"\n[{i}/{len(SEARCH_QUERIES)}] {query}")
        results = search_with_serpapi(query)
        
        if results:
            all_results.extend(results)
            print(f"   ✓ Trovati {len(results)} risultati")
        else:
            print(f"   ⚠ Nessun risultato")
    
    print(f"\n📊 Totale risultati: {len(all_results)}")
    
    if len(all_results) == 0:
        print("\n❌ Nessun risultato trovato")
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
    
    # Prova Gemini prima
    notizie = []
    if has_gemini:
        print("\n🧠 Analisi con Gemini AI...")
        analyzed = analyze_with_gemini(unique_results)
        if analyzed:
            notizie = analyzed.get('notizie', [])
    
    # Se Gemini fallisce, usa analisi locale
    if not notizie:
        print("\n🔧 Uso analisi locale avanzata...")
        analyzed = analyze_locally_enhanced(unique_results)
        notizie = analyzed.get('notizie', [])
    
    if notizie:
        notizie.sort(key=lambda x: x.get('importanza', 0), reverse=True)
        save_results(notizie[:15])
        
        print(f"\n✨ Salvate {len(notizie[:15])} notizie!")
        
        cat_count = {}
        for news in notizie[:15]:
            cat = news.get('categoria', 'Altro')
            cat_count[cat] = cat_count.get(cat, 0) + 1
        
        print("\n📊 Distribuzione:")
        for cat, count in cat_count.items():
            print(f"   • {cat}: {count}")
        
        print("\n📰 Top 5:")
        for i, news in enumerate(notizie[:5], 1):
            print(f"{i}. [{news.get('importanza')}/10] {news.get('categoria')}")
            print(f"   {news.get('titolo')[:75]}...")
    else:
        print("\n⚠️ Nessuna notizia rilevante")
        save_results([])
    
    print("\n✅ Completato!")

if __name__ == "__main__":
    main()
