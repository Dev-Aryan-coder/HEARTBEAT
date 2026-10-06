import nltk
import logging

# Configure logging
logger = logging.getLogger("HEARTBEAT_NLTK")

def ensure_nltk_data():
    """ISSUE 8.1 FIX: Ensures required NLTK data is available without silent crashes."""
    required_packages = [
        ('punkt', 'tokenizers/punkt'),
        ('stopwords', 'corpora/stopwords'),
        ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
        ('punkt_tab', 'tokenizers/punkt_tab') # Needed for newer NLTK versions
    ]
    
    for package, lookup in required_packages:
        try:
            nltk.data.find(lookup)
            # logger.debug(f"NLTK package '{package}' already available.")
        except LookupError:
            logger.info(f"Downloading NLTK package '{package}'...")
            try:
                nltk.download(package, quiet=True)
            except Exception as e:
                logger.error(f"Failed to download NLTK package '{package}': {str(e)}")

# Initialize on import
ensure_nltk_data()
