import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { type, notebookId, urls, title, content, timestamp, sourceIds } = await req.json();
    
    console.log(`Process additional sources received ${type} request for notebook ${notebookId}`);

    const backendUrl = Deno.env.get('PYTHON_BACKEND_URL');
    if (!backendUrl) {
      throw new Error('PYTHON_BACKEND_URL environment variable not set');
    }

    let payload;
    
    if (type === 'multiple-websites') {
      payload = {
        type: 'multiple-websites',
        notebookId,
        urls,
        sourceIds,
      };
    } else if (type === 'copied-text') {
      payload = {
        type: 'copied-text',
        notebookId,
        title,
        content,
        sourceIds,
      };
    } else {
      throw new Error(`Unsupported type: ${type}`);
    }

    console.log('Sending payload:', JSON.stringify(payload, null, 2));

    const response = await fetch(`${backendUrl}/sources/process-additional`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.get('Authorization'),
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend request failed:', response.status, errorText);
      throw new Error(`Backend request failed: ${response.status} - ${errorText}`);
    }

    const responseData = await response.json();
    console.log('Backend response:', responseData);

    return new Response(JSON.stringify({ 
      success: true, 
      message: `${type} data sent to backend successfully`,
      responseData 
    }), {
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders 
      },
    });

  } catch (error) {
    console.error('Process additional sources error:', error);
    
    return new Response(JSON.stringify({ 
      error: error.message,
      success: false 
    }), {
      status: 500,
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders 
      },
    });
  }
});