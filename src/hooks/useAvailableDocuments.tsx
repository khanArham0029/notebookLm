import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

export interface AvailableDocument {
  id: string;
  title: string;
  type: 'pdf' | 'text' | 'website' | 'youtube' | 'audio';
  content?: string;
  summary?: string;
  url?: string;
  file_path?: string;
  metadata?: any;
  created_at: string;
}

export const useAvailableDocuments = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch all available documents from the database
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['available-documents'],
    queryFn: async () => {
      // For now, we'll fetch from sources table where they're not assigned to any notebook
      // In a real implementation, you might have a separate 'available_documents' table
      const { data, error } = await supabase
        .from('sources')
        .select('*')
        .is('notebook_id', null) // Documents not assigned to any notebook
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data as AvailableDocument[];
    },
    enabled: !!user,
  });

  // Add selected document to a notebook
  const addDocumentToNotebook = useMutation({
    mutationFn: async ({ documentId, notebookId }: { documentId: string; notebookId: string }) => {
      if (!user) throw new Error('User not authenticated');

      // Get the original document
      const { data: originalDoc, error: fetchError } = await supabase
        .from('sources')
        .select('*')
        .eq('id', documentId)
        .single();

      if (fetchError) throw fetchError;

      // Create a copy of the document for this notebook
      const { data, error } = await supabase
        .from('sources')
        .insert({
          notebook_id: notebookId,
          title: originalDoc.title,
          type: originalDoc.type,
          content: originalDoc.content,
          summary: originalDoc.summary,
          url: originalDoc.url,
          file_path: originalDoc.file_path,
          file_size: originalDoc.file_size,
          display_name: originalDoc.display_name,
          processing_status: 'completed', // Pre-existing documents are already processed
          metadata: originalDoc.metadata || {},
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      toast({
        title: "Document Added",
        description: "The document has been successfully added to your notebook.",
      });
      // Invalidate sources query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
    onError: (error) => {
      console.error('Failed to add document:', error);
      toast({
        title: "Error",
        description: "Failed to add document to notebook. Please try again.",
        variant: "destructive",
      });
    },
  });

  return {
    documents,
    isLoading,
    addDocumentToNotebook: addDocumentToNotebook.mutate,
    isAdding: addDocumentToNotebook.isPending,
  };
};