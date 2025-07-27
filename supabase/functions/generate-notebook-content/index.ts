import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { notebookId, filePath, sourceType, content } = await req.json()

    if (!notebookId || !sourceType) {
      return new Response(
        JSON.stringify({ error: 'notebookId and sourceType are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('Processing request:', { notebookId, filePath, sourceType });

    const backendUrl = Deno.env.get('PYTHON_BACKEND_URL');
    if (!backendUrl) {
      throw new Error('PYTHON_BACKEND_URL environment variable not set');
    }

    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    await supabaseClient
      .from('notebooks')
      .update({ generation_status: 'generating' })
      .eq('id', notebookId)

    const response = await fetch(`${backendUrl}/notebooks/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.get('Authorization'),
      },
      body: JSON.stringify({
        notebook_id: notebookId,
        source_type: sourceType,
        file_path: filePath,
        content: content,
      })
    });

    if (!response.ok) {
      console.error('Backend error:', response.status, response.statusText)
      const errorText = await response.text();
      console.error('Error response:', errorText);
      
      await supabaseClient
        .from('notebooks')
        .update({ generation_status: 'failed' })
        .eq('id', notebookId)

      return new Response(
        JSON.stringify({ error: 'Failed to generate content from backend' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const generatedData = await response.json()
    console.log('Generated data:', generatedData)

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Notebook content generated successfully' 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})