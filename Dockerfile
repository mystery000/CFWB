FROM python:3.10-alpine

# Switch to the app directory
WORKDIR /app

# Copy the Flask app files into the container
COPY app/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Expose the Flask app port
EXPOSE 5000

# Start the Flask app
ENTRYPOINT ["/entrypoint.sh"]