import os
import json
import requests
from datetime import datetime
import re

# Configurazione
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')

# Query organizzate per tipo
SEARCH_QUERIES = {
    'forum_problemi': [
        'site:practicalmachinist.com EDM problem',
        'site:practicalmachinist.com wire EDM failure',
        'site:cnczone.com EDM troubleshooting',
        'site:reddit.com/r/Machinists EDM issue',
        'EDM wire breaks frequently forum'
    ],
    'problemi_costruttore': [
        'Sodick EDM common problems',
        'GF Machining EDM issues',
        'Mitsubishi EDM failures',
        'Makino EDM malfunctions',
        'Fanuc EDM reliability problems'
    ],
    'richieste_features': [
        'EDM machine feature request forum',
        'wire EDM improvement suggestions',
        'EDM user wishlist',
        'EDM automation request'
    ],
    'novita_tech': [
        'Sodick new EDM machine 2025',
        'GF Machining Solutions announcement',
        'Mitsubishi EDM innovation',
        'EDM Industry 4.0 integration'
    ],
    'applicazioni': [
        'EDM aerospace applications',
        'medical device EDM case study',
        'automotive EDM tooling'
    ]
}

CATEGORIES = {
    'forum_problemi': 'Problemi e Soluzioni',
    'problemi_costruttore': 'Problemi per Costruttore',
    'richieste_features': 'Richieste Funzionalità',
    'novita_tech': 'Nuovi Modelli',
    'applicazioni': 'Applicazioni e Mercato'
}

CATEGORY_KEYWORDS = {
    'Problemi e Soluzioni': [
        'problem', 'issue', 'error', 'fail', 'break', 'malfunction',
        'troubleshoot', 'fix', 'repair', 'solution', 'help'
    ],
    'Problemi per Costruttore': [
        'sodick problem', 'mitsubishi issue', 'gf machining fault',
        'makino error', 'fanuc failure', 'reliability', 'defect'
    ],
    'Richieste Funzionalità': [
        'feature', 'request', 'wishlist', 'improvement', 'need',
        'want', 'should have', 'add', 'upgrade', 'enhancement'
    ],
    'Nuovi Modelli': [
        'new', 'launch', 'announce', 'introduce', 'release',
        'model', 'series', 'unveil'
    ],
    'Innovazioni Tecnologiche': [
        'innovation', 'technology', 'AI', 'automation', 'smart',
        'digital', 'IoT', 'advanced', 'breakthrough'
    ],
    'Eventi e Fiere': [
        'event', 'fair', 'exhibition', 'show', 'conference',
        'EMO', 'IMTS', 'JIMTOF'
    ],
    'Applicazioni e Mercato': [
        'aerospace', 'medical', 'automotive', 'application',
        'case study', 'manufacturing', 'production'
    ]
}

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
    """Usa Gemini se disponibile"""
    
    if not GOOGLE_API_KEY or len(all_results) == 0:
        return None
    
    content_summary = []
    for result in all_results[:25]:
        content_summary.append(
            f"Titolo: {result.get('title', '')}\n"
            f"Descrizione: {result.get('snippet', '')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Tipo: {result.get('search_type', 'generale')}\n"
        )
    
    combined_content = "\n---\n".join(content_summary)
    
    prompt = f"""Analizza questi contenuti da forum e siti EDM (Electrical Discharge Machining).

CONTENUTI:
{combined_content}

FOCUS PRIORITARIO:
1. PROBLEMI REALI degli utenti (rotture frequenti, malfunzionamenti)
2. PROBLEMI PER COSTRUTTORE (Sodick, Mitsubishi, GF Machining, Makino, Fanuc)
3. RICHIESTE FUNZIONALITÀ da parte degli utilizzatori
4. SOLUZIONI PRATICHE condivise nei forum
5. Nuovi modelli e innovazioni

Crea notizie in ITALIANO molto PRATICHE:
- Identifica problemi ricorrenti
- Specifica il costruttore se menzionato
- Indica soluzioni proposte
- Segnala richieste comuni degli utenti

CATEGORIE: 
- Problemi e Soluzioni (problemi generici)
- Problemi per Costruttore (problemi specifici per marca)
- Richieste Funzionalità (feature richieste)
- Nuovi Modelli
- Innovazioni Tecnologiche
- Applicazioni e Mercato

IMPORTANTE: Mantieni gli URL originali.

Rispondi in JSON:
{{
  "notizie": [
    {{
      "titolo": "Problema/Soluzione in italiano (specifica marca se presente)",
      "categoria": "categoria appropriata",
      "riassunto": "Descrizione pratica del problema/soluzione/richiesta",
      "importanza": 7,
      "fonte": "nome fonte",
      "data": "2025-10-23",
      "url": "URL originale",
      "costruttore": "nome marca se rilevante o null"
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
        
        return None
            
    except Exception as e:
        print(f"⚠️ Errore Gemini: {e}")
        return None

def categorize_smart(text, search_type=''):
    """Categorizzazione intelligente"""
    text_lower = text.lower()
    scores = {}
    
    # Boost categoria basato sul tipo di ricerca
    if search_type == 'forum_problemi':
        scores['Problemi e Soluzioni'] = 5
    elif search_type == 'problemi_costruttore':
        scores['Problemi per Costruttore'] = 5
    elif search_type == 'richieste_features':
        scores['Richieste Funzionalità'] = 5
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = scores.get(category, 0)
        score += sum(2 if keyword in text_lower else 0 for keyword in keywords)
        scores[category] = score
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    
    return 'Applicazioni e Mercato'

def extract_manufacturer(text):
    """Estrae il costruttore dal testo"""
    manufacturers = ['Sodick', 'Mitsubishi', 'GF Machining', 'Makino', 'Fanuc', 'Agie']
    text_lower = text.lower()
    
    for mfg in manufacturers:
        if mfg.lower() in text_lower:
            return mfg
    
    return None

def calculate_importance_smart(text, search_type=''):
    """Calcola importanza"""
    text_lower = text.lower()
    score = 5
    
    # Problemi reali sono molto importanti
    problem_keywords = ['break', 'fail', 'problem', 'issue', 'error', 'malfunction']
    if any(word in text_lower for word in problem_keywords):
        score += 2
    
    # Richieste feature sono importanti
    if 'request' in text_lower or 'need' in text_lower or 'want' in text_lower:
        score += 1
    
    # Forum post sono contenuti pratici
    if 'forum' in text_lower or 'reddit' in text_lower:
        score += 1
    
    # Costruttori noti
    brands = ['sodick', 'mitsubishi', 'gf machining', 'makino', 'fanuc']
    if any(brand in text_lower for brand in brands):
        score += 1
    
    return min(score, 10)

def clean_source(source):
    """Pulisce fonte"""
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
        search_type = result.get('search_type', '')
        
        categoria = categorize_smart(combined, search_type)
        importanza = calculate_importance_smart(combined, search_type)
        costruttore = extract_manufacturer(combined)
        
        url = result.get('url', '').strip()
        fonte = clean_source(result.get('source', 'Web'))
        
        notizia = {
            'titolo': title[:120],
            'categoria': categoria,
            'riassunto': snippet[:300],
            'importanza': importanza,
            'fonte': fonte,
            'data': result.get('date', datetime.now().strftime('%Y-%m-%d')),
            'url': url,
            'costruttore': costruttore
        }
        
        notizie.append(notizia)
    
    return {'notizie': notizie}

def save_results(notizie, filename='data/edm_news.json'):
    """Salva solo nuovi risultati (NO dati di esempio)"""
    os.makedirs('data', exist_ok=True)
    
    # NON caricare dati esistenti - ripartiamo sempre da zero
    # per evitare che i dati di esempio si ripropongano
    
    new_entry = {
        'timestamp': datetime.now().isoformat(),
        'data': {'notizie': notizie}
    }
    
    # Salva SOLO questa esecuzione
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([new_entry], f, indent=2, ensure_ascii=False)
    
    print(f"✅ Risultati salvati in {filename}")

def main():
    print("🤖 Avvio Agente EDM - Ricerca Forum e Problemi Reali")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not SERPAPI_KEY:
        print("❌ SERPAPI_KEY non configurata!")
        return
    
    has_gemini = bool(GOOGLE_API_KEY)
    print(f"✓ SerpAPI: Attivo")
    print(f"✓ Gemini AI: {'Attivo' if has_gemini else 'Non disponibile (uso analisi locale)'}")
    
    all_results = []
    
    # Ricerca per categoria
    for search_type, queries in SEARCH_QUERIES.items():
        print(f"\n📂 Categoria: {CATEGORIES.get(search_type, search_type)}")
        
        for query in queries:
            print(f"   🔍 {query[:60]}...")
            results = search_with_serpapi(query)
            
            if results:
                # Aggiungi il tipo di ricerca ai risultati
                for r in results:
                    r['search_type'] = search_type
                all_results.extend(results)
                print(f"      ✓ {len(results)} risultati")
            else:
                print(f"      ⚠ Nessun risultato")
    
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
    
    # Analisi
    notizie = []
    if has_gemini:
        print("\n🧠 Analisi con Gemini AI...")
        analyzed = analyze_with_gemini(unique_results)
        if analyzed:
            notizie = analyzed.get('notizie', [])
    
    if not notizie:
        print("\n🔧 Uso analisi locale avanzata...")
        analyzed = analyze_locally_enhanced(unique_results)
        notizie = analyzed.get('notizie', [])
    
    if notizie:
        notizie.sort(key=lambda x: x.get('importanza', 0), reverse=True)
        save_results(notizie[:20])  # Top 20
        
        print(f"\n✨ Salvate {len(notizie[:20])} notizie!")
        
        # Statistiche
        cat_count = {}
        mfg_count = {}
        for news in notizie[:20]:
            cat = news.get('categoria', 'Altro')
            cat_count[cat] = cat_count.get(cat, 0) + 1
            
            mfg = news.get('costruttore')
            if mfg:
                mfg_count[mfg] = mfg_count.get(mfg, 0) + 1
        
        print("\n📊 Distribuzione per categoria:")
        for cat, count in sorted(cat_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {cat}: {count}")
        
        if mfg_count:
            print("\n🏭 Costruttori menzionati:")
            for mfg, count in sorted(mfg_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {mfg}: {count}")
        
        print("\n📰 Top 5 notizie:")
        for i, news in enumerate(notizie[:5], 1):
            mfg_tag = f" [{news.get('costruttore')}]" if news.get('costruttore') else ""
            print(f"{i}. [{news.get('importanza')}/10] {news.get('categoria')}{mfg_tag}")
            print(f"   {news.get('titolo')[:70]}...")
    else:
        print("\n⚠️ Nessuna notizia rilevante")
        save_results([])
    
    print("\n✅ Completato!")

if __name__ == "__main__":
    main()
