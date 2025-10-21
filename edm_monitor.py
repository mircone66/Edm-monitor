import os
import json
import requests
from datetime import datetime
import re

SEARCH_QUERIES = [
    "EDM machine news 2025",
    "wire EDM innovation",
    "elettroerosione novità",
    "EDM technology breakthrough",
    "Sodick EDM new model",
    "GF Machining Solutions EDM",
    "Mitsubishi EDM updates"
]

CATEGORIES = [
    "Nuovi Modelli",
    "Innovazioni Tecnologiche", 
    "Aziende e Mercato",
    "Ricerca e Brevetti",
    "Eventi e Fiere"
]

# Keywords per categorizzazione automatica
CATEGORY_KEYWORDS = {
    "Nuovi Modelli": ["new model", "nuovo modello", "launch", "lancio", "release", "series"],
    "Innovazioni Tecnologiche": ["innovation", "technology", "breakthrough", "AI", "automation", "precision"],
    "Aziende e Mercato": ["company", "azienda", "market", "mercato", "acquisition", "expansion"],
    "Ricerca e Brevetti": ["patent", "brevetto", "research", "ricerca", "university", "study"],
    "Eventi e Fiere": ["event", "evento", "fair", "fiera", "exhibition", "conference", "EMO", "IMTS"]
}

def search_web(query):
    """Cerca informazioni usando DuckDuckGo"""
    url = "https://api.duckduckgo.com/"
    params = {
        'q': query,
        'format': 'json',
        'no_html': 1,
        'skip_disambig': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        
        # Estrai risultati
        if data.get('AbstractText'):
            results.append({
                'title': data.get('Heading', query),
                'snippet': data.get('AbstractText', ''),
                'url': data.get('AbstractURL', ''),
                'source': data.get('AbstractSource', 'DuckDuckGo')
            })
        
        # Aggiungi related topics
        for topic in data.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append({
                    'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' '),
                    'snippet': topic.get('Text', ''),
                    'url': topic.get('FirstURL', ''),
                    'source': 'DuckDuckGo'
                })
        
        return results
    except Exception as e:
        print(f"Errore ricerca per '{query}': {e}")
        return []

def categorize_text(text):
    """Categorizza il testo basandosi su keywords"""
    text_lower = text.lower()
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        scores[category] = score
    
    # Restituisci la categoria con punteggio più alto
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "Aziende e Mercato"  # Default

def calculate_importance(text):
    """Calcola importanza basata su keywords importanti"""
    important_keywords = [
        'breakthrough', 'revolutionary', 'first', 'new', 'innovation',
        'rivoluzionario', 'nuovo', 'innovazione', 'prima volta',
        'patent', 'award', 'record', 'fastest', 'best'
    ]
    
    text_lower = text.lower()
    score = 5  # Base score
    
    for keyword in important_keywords:
        if keyword in text_lower:
            score += 1
    
    return min(score, 10)  # Max 10

def analyze_results(all_results):
    """Analizza i risultati senza usare AI esterna"""
    notizie = []
    
    for results in all_results:
        for result in results:
            if not result.get('snippet'):
                continue
            
            title = result.get('title', 'Notizia EDM')
            snippet = result.get('snippet', '')
            combined_text = f"{title} {snippet}"
            
            # Filtra solo se contiene termini EDM rilevanti
            edm_keywords = ['edm', 'elettroerosione', 'wire', 'machining', 'sodick', 'mitsubishi', 'gf machining']
            if not any(keyword in combined_text.lower() for keyword in edm_keywords):
                continue
            
            notizia = {
                'titolo': title[:100],  # Limita lunghezza
                'categoria': categorize_text(combined_text),
                'riassunto': snippet[:200],  # Prime 200 caratteri
                'importanza': calculate_importance(combined_text),
                'fonte': result.get('source', 'Web'),
                'data': datetime.now().strftime('%Y-%m-%d')
            }
            
            notizie.append(notizia)
    
    # Ordina per importanza
    notizie.sort(key=lambda x: x['importanza'], reverse=True)
    
    # Prendi solo le top 10
    return notizie[:10]

def save_results(data, filename='data/edm_news.json'):
    """Salva i risultati in un file JSON"""
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
        'data': {'notizie': data}
    }
    existing_data.append(new_entry)
    existing_data = existing_data[-100:]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Risultati salvati in {filename}")

def main():
    """Funzione principale"""
    print("🤖 Avvio Agente AI Monitoraggio EDM...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_results = []
    for query in SEARCH_QUERIES:
        print(f"🔍 Ricerca: {query}")
        results = search_web(query)
        if results:
            all_results.append(results)
            print(f"   Trovati {len(results)} risultati")
    
    print(f"\n📊 Totale ricerche completate: {len(all_results)}")
    
    print("\n🧠 Analisi e categorizzazione...")
    notizie = analyze_results(all_results)
    
    if notizie:
        save_results(notizie)
        print(f"\n✨ Trovate {len(notizie)} notizie rilevanti!")
        
        # Mostra preview
        print("\n📰 Preview notizie:")
        for i, news in enumerate(notizie[:3], 1):
            print(f"{i}. [{news['importanza']}/10] {news['titolo']}")
    else:
        print("\n⚠️ Nessuna notizia rilevante trovata in questa ricerca")
        # Salva comunque un placeholder
        save_results([])
    
    print("\n✅ Agente completato!")

if __name__ == "__main__":
    main()
