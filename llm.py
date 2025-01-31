from transformers import pipeline

classifier = pipeline("sentiment-analysis")
result = classifier("You're a cuckold, you bastard!")
print(result)
