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
    const { session_id, message, user_id } = await req.json();
    
    console.log('Received message:', { session_id, message, user_id });

    const backendUrl = Deno.env.get('PYTHON_BACKEND_URL');
    if (!backendUrl) {
      throw new Error('PYTHON_BACKEND_URL environment variable not set');
    }

    const response = await fetch(`${backendUrl}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': req.headers.get('Authorization'),
      },
      body: JSON.stringify({
        session_id,
        message,
        user_id,
      })
    });

    if (!response.ok) {
      console.error(`Backend responded with status: ${response.status}`);
      const errorText = await response.text();
      console.error('Backend error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const responseData = await response.json();
    console.log('Backend response:', responseData);

    return new Response(
      JSON.stringify({ success: true, data: responseData }),
      { 
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        } 
      }
    );

  } catch (error) {
    console.error('Error in send-chat-message:', error);
    
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Failed to send message to backend' 
      }),
      { 
        status: 500,
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        }
      }
    );
  }
});