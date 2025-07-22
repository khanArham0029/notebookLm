
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { useEffect } from 'react';

export const useSources = (notebookId?: string) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const {
    data: sources = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['sources', notebookId],
    queryFn: async () => {
      if (!notebookId) return [];
      
      const { data, error } = await supabase
        .from('sources')
        .select('*')
        .eq('notebook_id', notebookId)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data;
    },
    enabled: !!notebookId,
  });

  // Set up Realtime subscription for sources table
  useEffect(() => {
    if (!notebookId || !user) return;

    console.log('Setting up Realtime subscription for sources table, notebook:', notebookId);

    const channel = supabase
      .channel('sources-changes')
      .on(
        'postgres_changes',
        {
          event: '*', // Listen to all events (INSERT, UPDATE, DELETE)
          schema: 'public',
          table: 'sources',
          filter: `notebook_id=eq.${notebookId}`
        },
        (payload: any) => {
          console.log('Realtime: Sources change received:', payload);
          
          // Update the query cache based on the event type
          queryClient.setQueryData(['sources', notebookId], (oldSources: any[] = []) => {
            switch (payload.eventType) {
              case 'INSERT':
                // Add new source if it doesn't already exist
                const newSource = payload.new as any;
                const existsInsert = oldSources.some(source => source.id === newSource?.id);
                if (existsInsert) {
                  console.log('Source already exists, skipping INSERT:', newSource?.id);
                  return oldSources;
                }
                console.log('Adding new source to cache:', newSource);
                return [newSource, ...oldSources];
                
              case 'UPDATE':
                // Update existing source
                const updatedSource = payload.new as any;
                console.log('Updating source in cache:', updatedSource?.id);
                return oldSources.map(source => 
                  source.id === updatedSource?.id ? updatedSource : source
                );
                
              case 'DELETE':
                // Remove deleted source
                const deletedSource = payload.old as any;
                console.log('Removing source from cache:', deletedSource?.id);
                return oldSources.filter(source => source.id !== deletedSource?.id);
                
              default:
                console.log('Unknown event type:', payload.eventType);
                return oldSources;
            }
          });
        }
      )
      .subscribe((status) => {
        console.log('Realtime subscription status for sources:', status);
      });

    return () => {
      console.log('Cleaning up Realtime subscription for sources');
      supabase.removeChannel(channel);
    };
  }, [notebookId, user, queryClient]);


  const updateSource = useMutation({
    mutationFn: async ({ sourceId, updates }: { 
      sourceId: string; 
      updates: { 
        title?: string;
        file_path?: string;
        processing_status?: string;
      }
    }) => {
      const { data, error } = await supabase
        .from('sources')
        .update(updates)
        .eq('id', sourceId)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // The Realtime subscription will handle updating the cache
    },
  });

  return {
    sources,
    isLoading,
    error,
    updateSource: updateSource.mutate,
    isUpdating: updateSource.isPending,
  };
};
