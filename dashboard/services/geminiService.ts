import { GoogleGenAI } from "@google/genai";

// Initialize the API client
// Note: In a real production app, this key would come from a secure backend proxy or 
// be injected via environment variables. For this demo, we assume it's available.
// If the user hasn't set it in the UI, calls will fail gracefully.

export const generateProjectFile = async (
  apiKey: string,
  fileType: 'README' | 'SPEC',
  repoName: string,
  description: string
): Promise<string> => {
  if (!apiKey) {
    throw new Error("API Key is missing. Please configure it in settings.");
  }

  const ai = new GoogleGenAI({ apiKey });
  
  const modelId = 'gemini-2.5-flash';
  
  let prompt = "";
  if (fileType === 'README') {
    prompt = `Create a comprehensive README.md for a GitHub repository named "${repoName}". 
    Project Description: ${description}. 
    Include sections for Installation, Usage, Features, and Contributing. Use Markdown format.`;
  } else {
    prompt = `Create a detailed technical specification (spec.md) for a software project named "${repoName}".
    Project Context: ${description}.
    Include Functional Requirements, Non-Functional Requirements, API Endpoints, and Data Models. Use Markdown format.`;
  }

  try {
    const response = await ai.models.generateContent({
      model: modelId,
      contents: prompt,
      config: {
        thinkingConfig: { thinkingBudget: 0 } // Disable thinking for faster generation
      }
    });

    return response.text || "Failed to generate content.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw error;
  }
};