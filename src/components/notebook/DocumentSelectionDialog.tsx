import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { FileText, Globe, Video, Mic, Plus, Check } from 'lucide-react';
import { useAvailableDocuments } from '@/hooks/useAvailableDocuments';

interface DocumentSelectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  notebookId?: string;
}

const DocumentSelectionDialog = ({
  open,
  onOpenChange,
  notebookId
}: DocumentSelectionDialogProps) => {
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const { documents, isLoading, addDocumentToNotebook, isAdding } = useAvailableDocuments();

  const getDocumentIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FileText className="h-5 w-5 text-red-600" />;
      case 'text':
        return <FileText className="h-5 w-5 text-gray-600" />;
      case 'website':
        return <Globe className="h-5 w-5 text-blue-600" />;
      case 'youtube':
        return <Video className="h-5 w-5 text-red-600" />;
      case 'audio':
        return <Mic className="h-5 w-5 text-purple-600" />;
      default:
        return <FileText className="h-5 w-5 text-gray-600" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'pdf':
        return 'PDF';
      case 'text':
        return 'Text';
      case 'website':
        return 'Website';
      case 'youtube':
        return 'YouTube';
      case 'audio':
        return 'Audio';
      default:
        return 'Document';
    }
  };

  const toggleDocumentSelection = (documentId: string) => {
    const newSelection = new Set(selectedDocuments);
    if (newSelection.has(documentId)) {
      newSelection.delete(documentId);
    } else {
      newSelection.add(documentId);
    }
    setSelectedDocuments(newSelection);
  };

  const handleAddSelectedDocuments = async () => {
    if (!notebookId || selectedDocuments.size === 0) return;

    // Add each selected document to the notebook
    for (const documentId of selectedDocuments) {
      addDocumentToNotebook({ documentId, notebookId });
    }

    // Clear selection and close dialog
    setSelectedDocuments(new Set());
    onOpenChange(false);
  };

  const handleClose = () => {
    setSelectedDocuments(new Set());
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Plus className="h-5 w-5" />
            <span>Select Documents</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <p className="text-gray-600 text-sm">
              Choose from available documents to add to your notebook. You can select multiple documents at once.
            </p>
          </div>

          <ScrollArea className="h-[400px]">
            {isLoading ? (
              <div className="text-center py-8">
                <p className="text-gray-600">Loading available documents...</p>
              </div>
            ) : documents.length > 0 ? (
              <div className="grid grid-cols-1 gap-3 pr-4">
                {documents.map((document) => {
                  const isSelected = selectedDocuments.has(document.id);
                  return (
                    <Card
                      key={document.id}
                      className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                        isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                      }`}
                      onClick={() => toggleDocumentSelection(document.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3 flex-1">
                          <div className="flex-shrink-0 mt-1">
                            {getDocumentIcon(document.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-medium text-gray-900 truncate">
                                {document.title}
                              </h3>
                              <Badge variant="outline" className="text-xs">
                                {getTypeLabel(document.type)}
                              </Badge>
                            </div>
                            {document.summary && (
                              <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                                {document.summary}
                              </p>
                            )}
                            <p className="text-xs text-gray-500">
                              Added {new Date(document.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex-shrink-0 ml-3">
                          {isSelected ? (
                            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                              <Check className="h-4 w-4 text-white" />
                            </div>
                          ) : (
                            <div className="w-6 h-6 border-2 border-gray-300 rounded-full" />
                          )}
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
                  <FileText className="h-8 w-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No documents available</h3>
                <p className="text-sm text-gray-600">
                  There are no documents available to add to your notebook.
                </p>
              </div>
            )}
          </ScrollArea>

          <div className="flex justify-between items-center pt-4 border-t">
            <div className="text-sm text-gray-600">
              {selectedDocuments.size} document{selectedDocuments.size !== 1 ? 's' : ''} selected
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleAddSelectedDocuments}
                disabled={selectedDocuments.size === 0 || isAdding}
              >
                {isAdding ? 'Adding...' : `Add ${selectedDocuments.size} Document${selectedDocuments.size !== 1 ? 's' : ''}`}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DocumentSelectionDialog;