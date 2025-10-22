import os
import json
import requests
from datetime import datetime, timedelta
import re
from urllib.parse import quote_plus

# Configurazione
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Query mirate per trovare contenuti specifici
SEARCH_QUERIES = {
    'problemi_tecnici': [
        "EDM wire break problem solution",
        "EDM machine troubleshooting",
        "wire EDM surface finish issues",
        "EDM electrode wear problem"
    ],
    'novita_aziendali': [
        "Sodick new EDM machine 2025",
        "GF Machining Solutions announcement",
        "Mitsubishi EDM launch",
        "Makino wire EDM innovation"
    ],
    'trend_tecnologici': [
        "EDM automation AI",
        "wire EDM Industry 4.0",
        "EDM IoT connectivity",
        "smart EDM manufacturing"
    ],
    'eventi': [
        "EMO Hannover EDM",
        "IMTS EDM machines",
        "JIMTOF wire EDM",
        "EDM trade show 2025"
    ],
    'applicazioni': [
        "EDM aerospace components",
        "medical device EDM machining",
        "automotive EDM tooling",
        "EDM mold making"
    ]
}

# Siti specifici da cercare (usando site: search)
SPECIFIC_SITES = [
    "site:moderndmachineshop.com EDM",
    "site:manufacturingtomorrow.com electrical discharge",
    "site:industryweek.com EDM machining",
    "site:gfms.com/us news wire EDM",
    "site:sodick.com news",
    "site:mitsubishielectric.com EDM",
    "site:practicalmachinist.com EDM problem"
]

CATEGORIES = {
    'problemi_tecnici': 'Problemi e Soluzioni',
    'novita_aziendali': 'Nuovi Modelli',
    'trend_tecnologici': 'Innovazioni Tecnologiche',
    'eventi': 'Eventi e Fiere',
    'applicazioni': 'Applicazioni e Mercato'
}

def search_google_news(query, category='generale'):
    """Cerca notizie usando Google News RSS con query mirate"""
    try:
        # Usa query più specifiche per Google News
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
            descriptions = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', response.text)
            links = re.findall(r'<link>(.*?)</link>', response.text)
            pub_dates = re.findall(r'<pubDate>(.*?)</pubDate>', response.text)
            
            results = []
            for i in range(1, min(len(titles), 4)):  # Skip first (feed title), max 3
                title = titles[i] if i < len(titles) else ""
                desc = descriptions[i-1] if i-1 < len(descriptions) else title
                link = links[i] if i < len(links) else ""
                
                # Pulisci HTML
                desc_clean = re.sub(r'<.*?>', '', desc)
                
                results.append({
                    'title': title,
                    'snippet': desc_clean[:400],
                    'url': link,
                    'source': 'Google News',
                    'category': category,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            
            return results
        
    except Exception as e:
        print(f"   Errore: {e}")
    
    return []

def search_specific_sites():
    """Cerca direttamente su siti specializzati"""
    print("\n🎯 Ricerca su siti specializzati...")
    results = []
    
    for site_query in SPECIFIC_SITES[:3]:  # Limita a 3 per non sovraccaricare
        print(f"   • {site_query[:50]}...")
        site_results = search_google_news(site_query, 'siti_specializzati')
        if site_results:
            results.extend(site_results)
            print(f"     ✓ {len(site_results)} risultati")
        else:
            print(f"     ⚠ Nessun risultato")
    
    return results

def analyze_with_gemini(all_results):
    """Analizza con Gemini in modo più specifico"""
    
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY non configurata")
        return analyze_locally(all_results)
    
    if len(all_results) == 0:
        print("⚠️ Nessun articolo da analizzare")
        return {"notizie": []}
    
    # Prepara contenuto
    content_summary = []
    for result in all_results[:25]:
        content_summary.append(
            f"Categoria: {result.get('category', 'generale')}\n"
            f"Titolo: {result.get('title', '')}\n"
            f"Contenuto: {result.get('snippet', '')}\n"
        )
    
    combined_content = "\n---\n".join(content_summary)
    
    prompt = f"""Analizza questi articoli sulle macchine EDM (Electrical Discharge Machining).

ARTICOLI:
{combined_content}

FOCUS DELL'ANALISI:
1. PROBLEMI TECNICI: Identifica problemi comuni, troubleshooting, soluzioni
2. NOVITÀ AZIENDALI: Nuovi modelli, annunci, lanci prodotti
3. TREND TECNOLOGICI: Automazione, AI, Industry 4.0, innovazioni
4. EVENTI: Fiere, conferenze, trade show
5. APPLICAZIONI: Settori (aerospace, medical, automotive), case study

Per ogni notizia rilevante, crea:
- Titolo chiaro in ITALIANO (focus sul beneficio/problema)
- Categoria tra: Problemi e Soluzioni, Nuovi Modelli, Innovazioni Tecnologiche, Eventi e Fiere, Applicazioni e Mercato
- Riassunto pratico in ITALIANO (cosa significa per chi usa EDM?)
- Importanza 1-10 (10 = molto rilevante per utilizzatori EDM)

RISPOSTA IN JSON:
{{
  "notizie": [
    {{
      "titolo": "Titolo pratico in italiano",
      "categoria": "una delle 5 categorie",
      "riassunto": "Cosa significa per gli utilizzatori di EDM. Quali benefici o soluzioni offre.",
      "importanza": 8,
      "fonte": "nome fonte",
      "data": "2025-10-22",
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Rispondi SOLO con JSON valido."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 3000
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*', '', text).strip()
                
                result = json.loads(text)
                return result
        
        print(f"⚠️ Gemini API error: {response.status_code}")
        return analyze_locally(all_results)
            
    except Exception as e:
        print(f"⚠️ Errore Gemini: {e}")
        return analyze_locally(all_results)

def analyze_locally(results):
    """Analisi locale semplificata"""
    notizie = []
    
    for result in results:
        category = result.get('category', 'generale')
        mapped_cat = CATEGORIES.get(category, 'Applicazioni e Mercato')
        
        notizie.append({
            'titolo': result.get('title', 'Notizia EDM')[:120],
            'categoria': mapped_cat,
            'riassunto': result.get('snippet', '')[:300],
            'importanza': 6,
            'fonte': result.get('source', 'Web'),
            'data': result.get('date', datetime.now().strftime('%Y-%m-%d')),
            'tags': []
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
    print("🤖 Avvio Agente EDM - Ricerca Multi-Fonte Avanzata")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_results = []
    
    # Ricerca per categoria
    print("🔍 Ricerca per categoria...")
    for category, queries in SEARCH_QUERIES.items():
        print(f"\n📂 Categoria: {category}")
        for query in queries[:2]:  # Max 2 query per categoria
            print(f"   • {query}")
            results = search_google_news(query, category)
            if results:
                all_results.extend(results)
                print(f"     ✓ {len(results)} risultati")
            else:
                print(f"     ⚠ Nessun risultato")
    
    # Ricerca su siti specializzati
    site_results = search_specific_sites()
    all_results.extend(site_results)
    
    print(f"\n📊 Totale articoli raccolti: {len(all_results)}")
    
    if len(all_results) == 0:
        print("\n⚠️ Nessun articolo trovato")
        print("💡 Suggerimento: Le query potrebbero essere troppo specifiche o Google News potrebbe avere limitazioni")
        save_results([])
        return
    
    # Rimuovi duplicati
    seen_titles = set()
    unique_results = []
    for result in all_results:
        title_key = result['title'][:60].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_results.append(result)
    
    print(f"📊 Articoli unici dopo deduplicazione: {len(unique_results)}")
    
    # Analisi con Gemini
    print("\n🧠 Analisi intelligente con Gemini...")
    analyzed = analyze_with_gemini(unique_results)
    notizie = analyzed.get('notizie', [])
    
    if notizie:
        notizie.sort(key=lambda x: x.get('importanza', 0), reverse=True)
        
        save_results(notizie[:20])  # Top 20
        print(f"\n✨ Salvate {len(notizie[:20])} notizie!")
        
        # Statistiche per categoria
        cat_count = {}
        for news in notizie[:20]:
            cat = news.get('categoria', 'Altro')
            cat_count[cat] = cat_count.get(cat, 0) + 1
        
        print("\n📊 Distribuzione per categoria:")
        for cat, count in cat_count.items():
            print(f"   • {cat}: {count}")
        
        print("\n📰 Top 5 notizie:")
        for i, news in enumerate(notizie[:5], 1):
            print(f"{i}. [{news.get('importanza', 0)}/10] {news.get('categoria')}")
            print(f"   {news.get('titolo', 'N/A')[:80]}...")
    else:
        print("\n⚠️ Nessuna notizia rilevante dopo analisi")
        save_results([])
    
    print("\n✅ Agente completato!")

if __name__ == "__main__":
    main()
