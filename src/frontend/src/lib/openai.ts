// Frontend OpenAI client for direct API calls
const apiKey = import.meta.env.VITE_OPENAI_API_KEY;

if (!apiKey) {
  console.warn('VITE_OPENAI_API_KEY not found in environment variables');
}

export const chatWithOpenAI = async (message: string): Promise<string> => {
  try {
    if (!apiKey) {
      throw new Error('OpenAI API key not configured');
    }

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: 'Tu es un assistant IA pour SmartLinks, une plateforme de gestion de liens intelligents. Tu aides avec l\'analyse, la configuration et le dépannage du système.'
          },
          {
            role: 'user',
            content: message
          }
        ],
        max_tokens: 1000,
        temperature: 0.7,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices[0]?.message?.content || 'Désolé, je n\'ai pas pu générer une réponse.';
  } catch (error) {
    console.error('OpenAI API Error:', error);
    if (error instanceof Error) {
      return `Erreur OpenAI: ${error.message}`;
    }
    return 'Erreur lors de la communication avec OpenAI';
  }
};
