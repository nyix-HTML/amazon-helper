import os
from google import genai

# Client configuration using Gemini API key from environment variables
client = genai.Client()

THEME_STYLES = {
    'festive-red': {
        'border': 'border-red-900/60',
        'bg': 'bg-red-950/40',
        'badge': 'bg-red-900 text-red-200 border border-red-700'
    },
    'pine-green': {
        'border': 'border-emerald-900/60',
        'bg': 'bg-emerald-950/40',
        'badge': 'bg-emerald-900 text-emerald-200 border border-emerald-700'
    },
    'frozen-ice': {
        'border': 'border-sky-900/60',
        'bg': 'bg-sky-950/40',
        'badge': 'bg-sky-900 text-sky-200 border border-sky-700'
    },
    'golden-bell': {
        'border': 'border-amber-900/60',
        'bg': 'bg-amber-950/40',
        'badge': 'bg-amber-900 text-amber-200 border border-amber-700'
    }
}
