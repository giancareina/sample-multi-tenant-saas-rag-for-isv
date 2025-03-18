"""
Prompt templates for chat completion
"""

RAG_PROMPT_TEMPLATE = '''Use the context below to answer the question. Maintain a friendly, helpful tone.

Context:
{context}

Question: {query}

Important instructions:
1. If the provided context doesn't contain information relevant to the question, explicitly state this in your response.
2. Begin your response with "Based on the available information..." if the context is relevant.
3. Begin your response with "I don't have specific information about..." if the context is not relevant to the question.
4. Do not make up information that is not in the context.
5. If you need to speculate or provide general knowledge not in the context, clearly indicate this by saying "While not in the provided context, generally..."'''