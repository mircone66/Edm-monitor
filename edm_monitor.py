import os
import json
import requests
from datetime import datetime

# Configurazione
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Carica google-generativeai
try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
except ImportError:
    print("❌ Errore: google-generativeai non installato")
    exit(1)

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

def search_web(query):
    """Cerca informazioni sul web usando API di ricerca"""
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'found': True
        }
    except Exception as e:
        print(f"Errore ricerca per '{query}': {e}")
        return None

def analyze_with_ai(search_results):
    """Usa Gemini (Google) per analizzare e categorizzare i risultati"""
    
    prompt = f"""Analizza questi risultati di ricerca sulle macchine EDM (elettroerosione).
    
Risultati: {json.dumps(search_results, indent=2)}

Compiti:
1. Identifica le notizie più rilevanti e innovative
2. Categorizzale in: {', '.join(CATEGORIES)}
3. Crea un breve riassunto (2-3 righe) per ogni notizia
4. Assegna un punteggio di importanza (1-10)

Rispondi SOLO con un JSON valido in questo formato:
{{
  "notizie": [
    {{
      "titolo": "...",
      "categoria": "...",
      "riassunto": "...",
      "importanza": 8,
      "fonte": "...",
      "data": "..."
    }}
  ]
}}

NON includere testo al di fuori del JSON."""

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(response_text)
    except Exception as e:
        print(f"Errore analisi AI: {e}")
        return {"notizie": []}

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
        'data': data
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
    
    if not GOOGLE_API_KEY:
        print("❌ ERRORE: GOOGLE_API_KEY non configurata!")
        return
    
    all_results = []
    for query in SEARCH_QUERIES:
        print(f"🔍 Ricerca: {query}")
        result = search_web(query)
        if result:
            all_results.append(result)
    
    print(f"\n📊 Trovati {len(all_results)} risultati")
    
    print("\n🧠 Analisi con Gemini AI...")
    analyzed_data = analyze_with_ai(all_results)
    
    if analyzed_data.get('notizie'):
        save_results(analyzed_data)
        print(f"\n✨ Trovate {len(analyzed_data['notizie'])} notizie rilevanti!")
    else:
        print("\n⚠️ Nessuna notizia rilevante trovata in questa ricerca")
    
    print("\n✅ Agente completato!")

if __name__ == "__main__":
    main()
