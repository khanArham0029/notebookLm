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
    const { sourceId, filePath, notebookId } = await req.json()

    if (!sourceId || !filePath || !notebookId) {
      return new Response(
        JSON.stringify({ error: 'sourceId, filePath, and notebookId are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('Processing document:', { source_id: sourceId, file_path: filePath, notebook_id: notebookId });

    const backendUrl = Deno.env.get('PYTHON_BACKEND_URL');
    if (!backendUrl) {
      throw new Error('PYTHON_BACKEND_URL environment variable not set');
    }

    const response = await fetch(`${backendUrl}/documents/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.get('Authorization'),
      },
      body: JSON.stringify({
        file_path: filePath,
        source_id: sourceId,
        notebook_id: notebookId,
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend call failed:', response.status, errorText);
      
      const supabaseClient = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
      )

      await supabaseClient
        .from('sources')
        .update({ processing_status: 'failed' })
        .eq('id', sourceId)

      return new Response(
        JSON.stringify({ error: 'Document processing failed', details: errorText }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const result = await response.json()
    console.log('Backend response:', result);

    return new Response(
      JSON.stringify({ success: true, message: 'Document processing initiated', result }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error in process-document function:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})