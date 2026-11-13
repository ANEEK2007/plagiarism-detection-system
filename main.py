from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Read first document
with open("documents/document1.txt", "r") as file1:
    doc1 = file1.read()

# Read second document
with open("documents/document2.txt", "r") as file2:
    doc2 = file2.read() 

# Create TF-IDF Vectorizer

vectorizer = TfidfVectorizer()

# Convert text into numerical vectors

vectors = vectorizer.fit_transform([doc1, doc2])

# Calculate cosine similarity

similarity = cosine_similarity(vectors[0], vectors[1])

# Display result

percentage = similarity[0][0] * 100

print("\n===== PLAGIARISM DETECTION REPORT =====")

print(f"Document 1: document1.txt")
print(f"Document 2: document2.txt")

print(f"\nSimilarity: {percentage:.2f}%")

if percentage >= 70:
    print("Status: High Similarity")
elif percentage >= 40:
    print("Status: Moderate Similarity")
else:
    print("Status: Low Similarity")