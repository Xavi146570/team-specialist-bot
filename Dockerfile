1	FROM python:3.11-slim
     2	
     3	WORKDIR /app
     4	
     5	# Install dependencies
     6	COPY requirements.txt .
     7	RUN pip install --no-cache-dir -r requirements.txt
     8	
     9	# Copy application
    10	COPY . .
    11	
    12	# Run bot
    13	CMD ["python", "main.py"]
