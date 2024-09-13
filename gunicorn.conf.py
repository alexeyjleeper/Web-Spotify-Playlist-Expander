import os
import multiprocessing

# Use environment variables for binding
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

workers = multiprocessing.cpu_count() * 2 + 1
preload = True