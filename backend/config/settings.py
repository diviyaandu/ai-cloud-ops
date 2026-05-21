from dotenv import load_dotenv
import os

load_dotenv()

# Groq
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GROQ_MODEL     = "llama-3.1-8b-instant"

# Metric collection
METRICS_CACHE_TTL = 2       # seconds between psutil calls

# Analysis gating
ANALYSIS_COOLDOWN = 120     # min seconds between auto Groq calls
CHANGE_THRESHOLD  = 10      # % swing to consider metrics "significantly changed"

# Thresholds
CPU_WARN,  CPU_CRIT  = 60, 80
MEM_WARN,  MEM_CRIT  = 60, 80
DISK_WARN, DISK_CRIT = 70, 90