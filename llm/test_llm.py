from llm_client import generate


prompt = """
You are an information extraction system.

Extract the entities and relationship from the following text.

TEXT:
Cement shall conform to IS:12269-1987.

Return ONLY JSON.

Use exactly this format:

{
  "entities": [
    {
      "name": "entity name",
      "type": "entity type"
    }
  ],
  "relationships": [
    {
      "source": "source entity",
      "relation": "relationship",
      "target": "target entity"
    }
  ]
}
"""


result = generate(prompt)

print("=" * 70)
print("LLM RESPONSE")
print("=" * 70)

print(result)