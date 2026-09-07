import { GoogleGenAI, Type, Schema } from "@google/genai";
import { NextRequest, NextResponse } from "next/server";
import pdfParse from "pdf-parse";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const files = formData.getAll('files') as File[];

    if (!files || files.length === 0) {
      return NextResponse.json({ error: "No files uploaded" }, { status: 400 });
    }

    const documentTexts: { name: string; text: string }[] = [];

    for (const file of files) {
      try {
        const buffer = Buffer.from(await file.arrayBuffer());
        const data = await pdfParse(buffer);
        documentTexts.push({
          name: file.name,
          text: data.text,
        });
      } catch (err) {
        console.error(`Error parsing PDF ${file.name}:`, err);
        return NextResponse.json({ error: `Failed to parse PDF: ${file.name}. It might be corrupt.` }, { status: 400 });
      }
    }

    // Stage 1: Extraction
    const extractionSchema: Schema = {
      type: Type.ARRAY,
      items: {
        type: Type.OBJECT,
        properties: {
          fact_id: { type: Type.STRING },
          statement: { type: Type.STRING },
          metric_or_value: { type: Type.STRING },
          source_doc: { type: Type.STRING },
          verbatim_quote: { type: Type.STRING }
        },
        required: ["fact_id", "statement", "metric_or_value", "source_doc", "verbatim_quote"]
      }
    };

    let allFacts: any[] = [];
    
    const combinedTextContext = documentTexts.map(doc => `--- DOCUMENT: ${doc.name} ---\n${doc.text}`).join('\n\n');

    const extractionPrompt = `Extract key factual statements, metrics, and values from the following documents. 
    Ensure you preserve the exact verbatim quote and note the source document name.
    
    ${combinedTextContext}`;

    const extractionResponse = await ai.models.generateContent({
      model: "gemini-2.5-pro",
      contents: extractionPrompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: extractionSchema,
      }
    });

    const extractedFactsText = extractionResponse.text;
    if (!extractedFactsText) {
      throw new Error("No text returned from Gemini extraction");
    }
    allFacts = JSON.parse(extractedFactsText);

    // Stage 2: Reasoning
    const reasoningSchema: Schema = {
      type: Type.ARRAY,
      items: {
        type: Type.OBJECT,
        properties: {
          category: { type: Type.STRING, enum: ["Corroboration", "Contradiction", "Contextual Reconciliation", "Extraction Failure"] },
          competing_claims: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                statement: { type: Type.STRING },
                source_doc: { type: Type.STRING },
                verbatim_quote: { type: Type.STRING }
              },
              required: ["statement", "source_doc", "verbatim_quote"]
            }
          },
          reasoning: { type: Type.STRING, description: "Explanation of the relationship between the facts" },
          diagnostic_fix: { type: Type.STRING, description: "Suggested fix, only required for Extraction Failure" }
        },
        required: ["category", "competing_claims", "reasoning"]
      }
    };

    const reasoningPrompt = `Analyze the following extracted facts from multiple documents. Cross-reference them to find relationships.
    Group and classify the relationships into the following categories:
    - Corroboration: Facts confirmed across multiple documents.
    - Contradiction: Conflicting facts.
    - Contextual Reconciliation: Numbers or statements that appear to conflict but are resolved by differing timeframes, scopes, or units.
    - Extraction Failure: Honest extraction or reasoning failure (e.g., missing context, ambiguity).

    Facts:
    ${JSON.stringify(allFacts, null, 2)}`;

    const reasoningResponse = await ai.models.generateContent({
      model: "gemini-2.5-pro",
      contents: reasoningPrompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: reasoningSchema,
      }
    });

    const reasoningText = reasoningResponse.text;
    if (!reasoningText) {
      throw new Error("No text returned from Gemini reasoning");
    }
    const reasoningResults = JSON.parse(reasoningText);

    return NextResponse.json({ results: reasoningResults });

  } catch (error: any) {
    console.error("API Error:", error);
    return NextResponse.json({ error: error.message || "Internal Server Error" }, { status: 500 });
  }
}
